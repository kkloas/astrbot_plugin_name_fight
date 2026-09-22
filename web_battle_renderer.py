from __future__ import annotations

import base64
import json
import logging
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
import uuid
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import GifImagePlugin, Image, ImageChops
from websockets.sync.client import connect

logger = logging.getLogger(__name__)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _replay_fighter(fighter: dict[str, Any]) -> dict[str, Any]:
    martial_art = fighter.get("martial_art") or {}
    neigong = fighter.get("neigong") or {}
    qinggong = fighter.get("qinggong") or {}
    stats = fighter.get("stats") or {}
    return {
        "name": str(fighter.get("name") or "未知角色"),
        "stats": {
            "hp": int(stats.get("hp", 1)),
            "spd": float(stats.get("spd", 0)),
        },
        "currentHp": int(fighter.get("current_hp", stats.get("hp", 1))),
        "martialArt": {
            "id": martial_art.get("id", ""),
            "name": martial_art.get("name", "无名武学"),
            "type": martial_art.get("type", "sword"),
        },
        "neigong": {"id": neigong.get("id", ""), "name": neigong.get("name", "")},
        "qinggong": {"id": qinggong.get("id", ""), "name": qinggong.get("name", "")},
    }


def _battle_payload(
    fighter_a: dict[str, Any],
    fighter_b: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any] | None:
    events = result.get("events") if isinstance(result, dict) else None
    if not isinstance(events, list) or not events:
        return None
    payload = {
        "attacker": _replay_fighter(fighter_a),
        "defender": _replay_fighter(fighter_b),
        "winner": result.get("winner"),
        "events": events,
    }
    return payload


def _cdp_call(
    ws: Any, state: dict[str, int], method: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    state["id"] += 1
    request_id = state["id"]
    ws.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
    while True:
        message = json.loads(ws.recv(timeout=30))
        if message.get("id") == request_id:
            if "error" in message:
                raise RuntimeError(f"Chrome {method}: {message['error']}")
            return message


def _evaluate(ws: Any, state: dict[str, int], expression: str) -> Any:
    result = _cdp_call(
        ws,
        state,
        "Runtime.evaluate",
        {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        },
    )["result"]
    if "exceptionDetails" in result:
        raise RuntimeError(f"Battle export failed: {result['exceptionDetails']}")
    return result["result"].get("value")


def _devtools_endpoint(port: int) -> str:
    url = f"http://127.0.0.1:{port}/json"
    for _ in range(100):
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                pages = json.load(response)
            for page in pages:
                if page.get("type") == "page" and page.get("webSocketDebuggerUrl"):
                    return str(page["webSocketDebuggerUrl"])
        except (OSError, ValueError):
            pass
        time.sleep(0.05)
    raise RuntimeError("Chrome DevTools endpoint unavailable")


@contextmanager
def _browser():
    chrome = os.environ.get("NAME_FIGHT_CHROME", "/opt/google/chrome/chrome")
    if not Path(chrome).exists():
        chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser") or ""
    if not chrome:
        raise RuntimeError("Chrome is not installed")
    port = _free_port()
    with tempfile.TemporaryDirectory(prefix="namefight-chrome-") as profile_dir:
        process = subprocess.Popen(
            [
                chrome,
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                "--window-size=900,760",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-breakpad",
                "--allow-file-access-from-files",
                f"--user-data-dir={profile_dir}",
                f"--remote-debugging-port={port}",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            with connect(
                _devtools_endpoint(port), max_size=50_000_000, open_timeout=10
            ) as ws:
                state = {"id": 0}
                _cdp_call(ws, state, "Page.enable")
                yield ws, state
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _capture_frames(
    ws: Any, state: dict[str, int], page: Path, times: list[int], spool: Any
) -> list[tuple[int, int]]:
    _cdp_call(ws, state, "Page.navigate", {"url": page.as_uri()})
    for _ in range(100):
        if _evaluate(
            ws,
            state,
            f"location.href === {json.dumps(page.as_uri())} && document.body?.dataset.ready === '1' && typeof window.prepareExport === 'function'",
        ):
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("Web battle canvas did not finish loading")
    clip = _evaluate(ws, state, "window.prepareExport()")
    result = _cdp_call(
        ws,
        state,
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "captureBeyondViewport": True,
            "clip": clip,
        },
    )
    background = result["result"]["data"]
    _evaluate(ws, state, f"window.initializeExport({json.dumps(background)})")
    offsets = []
    for frame_time in times:
        data = base64.b64decode(
            _evaluate(ws, state, f"window.exportFrame({frame_time})")
        )
        offsets.append((spool.tell(), len(data)))
        spool.write(data)
    return offsets


def _read_frame(spool: Any, offset: tuple[int, int]) -> Image.Image:
    spool.seek(offset[0])
    with Image.open(BytesIO(spool.read(offset[1]))) as frame:
        return frame.convert("RGB")


def _write_gif(
    spool: Any, offsets: list[tuple[int, int]], durations: list[int], output_path: Path
) -> None:
    # Sample across every bout; reserve index 255 for unchanged pixels.
    count = min(24, len(offsets))
    samples = []
    for index in range(count):
        frame = _read_frame(
            spool, offsets[index * (len(offsets) - 1) // max(1, count - 1)]
        )
        frame.thumbnail((240, 180), Image.Resampling.BILINEAR)
        samples.append(frame)
    contact = Image.new("RGB", (240 * count, 180), "white")
    for index, frame in enumerate(samples):
        contact.paste(frame, (index * 240, 0))
    palette = contact.quantize(
        colors=127, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE
    )
    colors = palette.getpalette()[:381]
    colors += [0] * (381 - len(colors))
    # Pad unused slots with a duplicate color, keeping all opaque indices below 127.
    palette.putpalette(colors + colors[:3] * 129)
    # Different bouts can wrap their HUD text to different heights.
    width = height = 0
    for position, length in offsets:
        spool.seek(position)
        with Image.open(BytesIO(spool.read(min(length, 128)))) as frame:
            width, height = max(width, frame.width), max(height, frame.height)
    previous = None
    pending = None
    pending_duration = 0
    with output_path.open("wb") as output:

        def emit(frame: Image.Image, duration: int) -> None:
            nonlocal previous
            if previous is None:
                header, _ = GifImagePlugin.getheader(frame, info={"loop": 0})
                for block in header:
                    output.write(block)
                encoded = frame
                origin = (0, 0)
            else:
                # Compare palette indices, including colors with equal luminance.
                delta = ImageChops.difference(
                    Image.frombytes("L", frame.size, frame.tobytes()),
                    Image.frombytes("L", previous.size, previous.tobytes()),
                )
                box = delta.getbbox()
                if box is None:
                    return
                encoded = frame.crop(box)
                unchanged = delta.crop(box).point(
                    lambda value: 255 if value == 0 else 0
                )
                encoded.paste(255, mask=unchanged)
                origin = box[:2]
            for block in GifImagePlugin.getdata(
                encoded, offset=origin, duration=duration, disposal=1, transparency=255
            ):
                output.write(block)
            previous = frame

        for offset, duration in zip(offsets, durations):
            rgb = _read_frame(spool, offset)
            if rgb.size != (width, height):
                padded = Image.new("RGB", (width, height), "white")
                padded.paste(rgb, (0, 0))
                rgb = padded
            frame = rgb.quantize(palette=palette, dither=Image.Dither.NONE)
            # Keep the transparency slot out of opaque frame data.
            frame = frame.point(list(range(127)) + [0] * 129)
            frame.putpalette(palette.getpalette())
            if pending is not None and frame.tobytes() == pending.tobytes():
                pending_duration += duration
            else:
                if pending is not None:
                    emit(pending, pending_duration)
                pending, pending_duration = frame, duration
        if pending is not None:
            emit(pending, pending_duration)
        output.write(b";")


def _render_payloads(payloads: list[dict[str, Any]], data_dir: str) -> str | None:
    if not payloads:
        return None
    static_dir = Path(__file__).resolve().parent / "web_animation"
    template = static_dir / "index_hud.html"
    if not template.exists():
        return None
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(data_dir) / f"tmp_battle_{uuid.uuid4().hex[:8]}.gif"
    started = time.perf_counter()
    try:
        with (
            tempfile.TemporaryDirectory(prefix="namefight-render-") as work_dir,
            tempfile.SpooledTemporaryFile(max_size=32 * 1024 * 1024) as spool,
        ):
            offsets: list[tuple[int, int]] = []
            durations: list[int] = []
            with _browser() as (ws, state):
                for index, payload in enumerate(payloads):
                    inline = json.dumps(payload, ensure_ascii=True).replace(
                        "<", "\\u003c"
                    )
                    html = template.read_text(encoding="utf-8")
                    html = html.replace(
                        "<head>", f'<head><base href="{static_dir.as_uri()}/">', 1
                    )
                    html = html.replace(
                        '<script src="./battle-inline.js"></script>',
                        f"<script>window.__BATTLE__={inline};</script>",
                        1,
                    )
                    page = Path(work_dir) / f"battle-{index}.html"
                    page.write_text(html, encoding="utf-8")
                    duration = max(1900, int(payload["events"][-1].get("time", 1900)))
                    # GIF delays are centiseconds. 50 ms gives an exact 20 FPS.
                    duration = ((duration + 9) // 10) * 10
                    times = list(range(0, duration, 50)) + [duration]
                    offsets.extend(_capture_frames(ws, state, page, times, spool))
                    durations.extend([b - a for a, b in zip(times, times[1:])] + [500])
            captured = time.perf_counter()
            _write_gif(spool, offsets, durations, output_path)
        logger.info(
            "[name_fight] GIF frames=%d capture=%.2fs encode=%.2fs bytes=%d",
            len(offsets),
            captured - started,
            time.perf_counter() - captured,
            output_path.stat().st_size,
        )
        return str(output_path)
    except BaseException:
        output_path.unlink(missing_ok=True)
        raise


def render_battle_animation(
    fighter_a: dict[str, Any],
    fighter_b: dict[str, Any],
    result: dict[str, Any],
    data_dir: str,
    title: str = "江湖对决回放",
) -> str | None:
    del title
    payload = _battle_payload(fighter_a, fighter_b, result)
    return _render_payloads([payload], data_dir) if payload else None


def render_battle_sequence(
    segments: list[dict[str, Any]],
    data_dir: str,
    title: str = "江湖对决回放",
) -> str | None:
    del title
    payloads = []
    for segment in segments:
        payload = _battle_payload(
            segment.get("fighter_a") or {},
            segment.get("fighter_b") or {},
            segment.get("result") or {},
        )
        if payload is not None:
            payloads.append(payload)
    return _render_payloads(payloads, data_dir)
