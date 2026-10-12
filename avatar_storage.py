"""Bounded avatar imports from trusted local caches or public HTTP servers."""

import asyncio
import ipaddress
import os
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlsplit

import aiohttp
from aiohttp.resolver import DefaultResolver
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_PIXELS = 16_000_000


class PublicResolver(DefaultResolver):
    async def resolve(self, host, port=0, family=0):
        addresses = await super().resolve(host, port, family)
        if not addresses or any(
            not ipaddress.ip_address(address["host"]).is_global for address in addresses
        ):
            raise ValueError("Avatar URLs must resolve to public addresses")
        return addresses


def validate_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Unsupported avatar URL")
    if parsed.username or parsed.password or parsed.port not in {None, 80, 443}:
        raise ValueError("Unsupported avatar URL credentials or port")
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        return
    if not address.is_global:
        raise ValueError("Avatar URLs must use public addresses")


def read_local(path: Path, maximum_bytes: int) -> bytes:
    with path.open("rb") as handle:
        data = handle.read(maximum_bytes + 1)
    if len(data) > maximum_bytes:
        raise ValueError("Avatar file exceeds the size limit")
    return data


def normalize_image(data: bytes, target: Path) -> None:
    try:
        with Image.open(BytesIO(data)) as image:
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("Avatar dimensions exceed the limit")
            image.seek(0)
            image.load()
            image = image.convert("RGB")
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor, name = tempfile.mkstemp(prefix="avatar-", dir=target.parent)
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    image.save(handle, format="JPEG", quality=90)
                Path(name).replace(target)
            finally:
                Path(name).unlink(missing_ok=True)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Avatar must be a valid image") from exc


async def save_avatar(
    reference: str,
    target: Path,
    *,
    allowed_roots: list[Path],
    maximum_bytes: int,
) -> None:
    parsed = urlsplit(reference)
    if parsed.scheme in {"http", "https"}:
        validate_url(reference)
        resolver = PublicResolver()
        try:
            connector = aiohttp.TCPConnector(resolver=resolver)
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=15),
                trust_env=False,
                auto_decompress=False,
            ) as session:
                async with session.get(reference, allow_redirects=False) as response:
                    if response.status != 200:
                        raise ValueError(
                            "Avatar download failed or attempted a redirect"
                        )
                    if (
                        response.content_length
                        and response.content_length > maximum_bytes
                    ):
                        raise ValueError("Avatar file exceeds the size limit")
                    data = bytearray()
                    async for chunk in response.content.iter_chunked(65536):
                        data.extend(chunk)
                        if len(data) > maximum_bytes:
                            raise ValueError("Avatar file exceeds the size limit")
        finally:
            await resolver.close()
    else:
        if parsed.scheme not in {"", "file"} or parsed.netloc:
            raise ValueError("Unsupported local avatar reference")
        path = Path(unquote(parsed.path) if parsed.scheme else reference).resolve()
        if not any(path.is_relative_to(root.resolve()) for root in allowed_roots):
            raise ValueError(
                "Avatar files must come from the AstrBot temporary directory"
            )
        data = await asyncio.to_thread(read_local, path, maximum_bytes)
    if not data:
        raise ValueError("Avatar image is empty")
    await asyncio.to_thread(normalize_image, bytes(data), target)
