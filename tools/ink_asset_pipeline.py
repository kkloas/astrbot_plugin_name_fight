# -*- coding: utf-8 -*-
"""Local lossless ink VFX image processing and sprite-sheet packing pipeline."""

from __future__ import annotations

import argparse
import glob
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image


def white_to_alpha_rgba(
    rgb_img: Image.Image,
    white_threshold: int = 246,
    gamma: float = 0.92,
) -> Image.Image:
    """Convert pure-white-background sumi-e artwork into decontaminated RGBA."""
    rgb = np.asarray(rgb_img.convert("RGB"), dtype=np.float32) / 255.0
    dist = 1.0 - rgb
    raw_alpha = np.max(dist, axis=2)

    floor = max(0.0, (255.0 - float(white_threshold)) / 255.0)
    span = max(1e-6, 1.0 - floor)
    scaled = np.clip((raw_alpha - floor) / span, 0.0, 1.0)
    alpha = np.where(raw_alpha <= floor, 0.0, np.clip(np.power(scaled, gamma), 0.0, 1.0))

    denom = np.maximum(alpha, 1e-4)[..., None]
    clean_rgb = np.where(
        alpha[..., None] > 0.0,
        np.clip(1.0 - dist / denom, 0.0, 1.0),
        0.0,
    )

    rgba = np.empty((rgb.shape[0], rgb.shape[1], 4), dtype=np.uint8)
    rgba[..., :3] = np.round(clean_rgb * 255.0).astype(np.uint8)
    rgba[..., 3] = np.round(alpha * 255.0).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")


def black_to_alpha_rgba(
    rgb_img: Image.Image,
    black_threshold: int = 12,
    gamma: float = 0.92,
) -> Image.Image:
    """Convert pure-black-background luminous/venom VFX artwork into decontaminated RGBA.

    Preserves opaque milky-white cores while keeping mid-tone/outer contours as rich
    cyan-teal (#0d9488 / #14b8a6) instead of over-bleaching them to pale white,
    so the resulting RGBA reads crisply on BOTH light rice-paper and dark backdrops.
    """
    rgb = np.asarray(rgb_img.convert("RGB"), dtype=np.float32) / 255.0
    raw_alpha = np.max(rgb, axis=2)

    floor = max(0.0, float(black_threshold) / 255.0)
    span = max(1e-6, 1.0 - floor)
    scaled = np.clip((raw_alpha - floor) / span, 0.0, 1.0)
    alpha = np.where(raw_alpha <= floor, 0.0, np.clip(np.power(scaled, gamma * 0.72), 0.0, 1.0))

    denom = np.maximum(raw_alpha, 1e-4)[..., None]
    unpremult = np.where(alpha[..., None] > 0.0, np.clip(rgb / denom, 0.0, 1.0), 0.0)

    # Cyan-teal contour anchor (#0d9488 -> rgb(0.051, 0.580, 0.533)) for mid-tones & cyan edges
    # so white venom has a rich cyan-teal edge/scale definition on pale rice-paper backgrounds.
    cyan_bias = np.clip((unpremult[..., 1] - unpremult[..., 0]) * 1.8, 0.0, 1.0)
    edge_weight = np.clip(1.0 - np.power(scaled, 1.35), 0.0, 1.0)
    teal_mix = np.clip(np.maximum(cyan_bias * 0.78, edge_weight * 0.85), 0.0, 0.92)[..., None]
    teal_rgb = np.array([13.0 / 255.0, 148.0 / 255.0, 136.0 / 255.0], dtype=np.float32)
    clean_rgb = np.where(
        alpha[..., None] > 0.0,
        np.clip(unpremult * (1.0 - teal_mix) + teal_rgb * teal_mix, 0.0, 1.0),
        0.0,
    )

    rgba = np.empty((rgb.shape[0], rgb.shape[1], 4), dtype=np.uint8)
    rgba[..., :3] = np.round(clean_rgb * 255.0).astype(np.uint8)
    rgba[..., 3] = np.round(alpha * 255.0).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")


def crop_and_pad_rgba(
    rgba_img: Image.Image,
    crop_pad: int = 32,
    max_width: int = 2048,
) -> Image.Image:
    """Trim transparent borders, restore even margin, and bound max width."""
    alpha_arr = np.asarray(rgba_img.getchannel("A"), dtype=np.float32) / 255.0
    mask = alpha_arr > 0.01
    if np.any(mask):
        ys, xs = np.where(mask)
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        cropped = rgba_img.crop((x0, y0, x1, y1))
    else:
        cropped = rgba_img

    if crop_pad > 0:
        padded = Image.new(
            "RGBA",
            (cropped.width + crop_pad * 2, cropped.height + crop_pad * 2),
            (0, 0, 0, 0),
        )
        padded.paste(cropped, (crop_pad, crop_pad))
    else:
        padded = cropped

    if max_width > 0 and padded.width > max_width:
        target_h = max(1, int(round(padded.height * (max_width / padded.width))))
        padded = padded.resize((max_width, target_h), Image.Resampling.LANCZOS)
    return padded


def cmd_white_to_alpha(args: argparse.Namespace) -> None:
    src = Path(args.input)
    dst = Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        rgba = white_to_alpha_rgba(
            img,
            white_threshold=args.white_threshold,
            gamma=args.gamma,
        )
    out = crop_and_pad_rgba(rgba, crop_pad=args.crop_pad, max_width=args.max_width)
    out.save(dst, format="PNG", optimize=True)

    alpha_arr = np.asarray(out.getchannel("A"), dtype=np.uint8)
    coverage = float(np.mean(alpha_arr > 2))
    print(
        f"Saved {dst.as_posix()}: {out.width}x{out.height}, mode={out.mode}, "
        f"coverage={coverage:.2%}, bytes={dst.stat().st_size}"
    )


def cmd_black_to_alpha(args: argparse.Namespace) -> None:
    src = Path(args.input)
    dst = Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        rgba = black_to_alpha_rgba(
            img,
            black_threshold=args.black_threshold,
            gamma=args.gamma,
        )
    out = crop_and_pad_rgba(rgba, crop_pad=args.crop_pad, max_width=args.max_width)
    out.save(dst, format="PNG", optimize=True)

    alpha_arr = np.asarray(out.getchannel("A"), dtype=np.uint8)
    coverage = float(np.mean(alpha_arr > 2))
    print(
        f"Saved {dst.as_posix()}: {out.width}x{out.height}, mode={out.mode}, "
        f"coverage={coverage:.2%}, bytes={dst.stat().st_size}"
    )


def _resolve_frames(pattern_or_dir: str) -> list[Path]:
    candidate = Path(pattern_or_dir)
    if candidate.is_dir():
        exts = {".png", ".jpg", ".jpeg", ".webp"}
        files = [p for p in candidate.iterdir() if p.is_file() and p.suffix.lower() in exts]
        return sorted(files, key=lambda p: p.name)
    matched = [Path(p) for p in glob.glob(pattern_or_dir) if Path(p).is_file()]
    return sorted(matched, key=lambda p: p.name)


def _convert_frame(img: Image.Image, args: argparse.Namespace) -> Image.Image:
    if args.mode == "white":
        return white_to_alpha_rgba(
            img,
            white_threshold=args.white_threshold,
            gamma=args.gamma,
        )
    if args.mode == "black":
        return black_to_alpha_rgba(img, gamma=args.gamma)
    return img.convert("RGBA")


def cmd_pack_sheet(args: argparse.Namespace) -> None:
    frames = _resolve_frames(args.input)
    if not frames:
        raise SystemExit(f"No matching frames found for: {args.input}")

    processed: list[Image.Image] = []
    target_h = None
    for path in frames:
        with Image.open(path) as img:
            rgba = _convert_frame(img, args)
            if target_h is None:
                target_h = max(1, int(round(rgba.height * (args.frame_width / max(1, rgba.width)))))
            resized = rgba.resize((args.frame_width, target_h), Image.Resampling.LANCZOS)
            processed.append(resized)

    assert target_h is not None
    sheet = Image.new("RGBA", (args.frame_width * len(processed), target_h), (0, 0, 0, 0))
    for idx, frame in enumerate(processed):
        sheet.paste(frame, (idx * args.frame_width, 0))

    dst = Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dst, format="PNG", optimize=True)
    print(
        f"Packed {len(processed)} frames -> {dst.as_posix()}: "
        f"{sheet.width}x{sheet.height} (frame={args.frame_width}x{target_h}), "
        f"mode={sheet.mode}, bytes={dst.stat().st_size}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ink VFX asset processing pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p_white = sub.add_parser("white-to-alpha", help="Convert pure white background ink art to RGBA PNG")
    p_white.add_argument("input", help="Input image file path")
    p_white.add_argument("output", help="Output RGBA PNG path")
    p_white.add_argument("--white-threshold", type=int, default=246, help="0-255 white cutoff threshold")
    p_white.add_argument("--gamma", type=float, default=0.92, help="Alpha gamma curve")
    p_white.add_argument("--crop-pad", type=int, default=32, help="Transparent margin padding in px")
    p_white.add_argument("--max-width", type=int, default=2048, help="Max output width in px")
    p_white.set_defaults(func=cmd_white_to_alpha)

    p_black = sub.add_parser("black-to-alpha", help="Convert pure black background luminous art to RGBA PNG")
    p_black.add_argument("input", help="Input image file path")
    p_black.add_argument("output", help="Output RGBA PNG path")
    p_black.add_argument("--black-threshold", type=int, default=14, help="0-255 black cutoff threshold")
    p_black.add_argument("--gamma", type=float, default=0.90, help="Alpha gamma curve")
    p_black.add_argument("--crop-pad", type=int, default=32, help="Transparent margin padding in px")
    p_black.add_argument("--max-width", type=int, default=1800, help="Max output width in px")
    p_black.set_defaults(func=cmd_black_to_alpha)

    p_pack = sub.add_parser("pack-sheet", help="Pack frame sequence into horizontal RGBA sprite sheet")
    p_pack.add_argument("input", help="Input directory or glob pattern")
    p_pack.add_argument("output", help="Output sprite-sheet PNG path")
    p_pack.add_argument("--mode", choices=("rgba", "white", "black"), default="white")
    p_pack.add_argument("--frame-width", type=int, default=480)
    p_pack.add_argument("--white-threshold", type=int, default=246)
    p_pack.add_argument("--gamma", type=float, default=0.92)
    p_pack.set_defaults(func=cmd_pack_sheet)
    return parser


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    args.func(args)


if __name__ == "__main__":
    main()
