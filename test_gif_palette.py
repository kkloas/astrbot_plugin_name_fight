"""Verify color retention and delta-frame decoding without browser or player data."""

import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image
from web_battle_renderer import _write_gif


class GifPaletteTests(unittest.TestCase):
    def encode(self, frames, durations):
        with tempfile.TemporaryDirectory() as directory, BytesIO() as spool:
            offsets = []
            for frame in frames:
                start = spool.tell()
                frame.save(spool, format="PNG")
                offsets.append((start, spool.tell() - start))
            path = Path(directory) / "test.gif"
            _write_gif(spool, offsets, durations, path)
            with Image.open(path) as gif:
                decoded, delays = [], []
                for index in range(gif.n_frames):
                    gif.seek(index)
                    decoded.append(gif.convert("RGB"))
                    delays.append(gif.info["duration"])
            return decoded, delays

    def test_colored_effects_survive_gray_background_and_frame_deltas(self):
        background = Image.new("RGB", (240, 180))
        background.putdata(
            [
                (v, v, v)
                for y in range(180)
                for x in range(240)
                for v in [(x + y) % 170 + 45]
            ]
        )
        colors = [(230, 35, 40), (25, 200, 70), (135, 35, 225), (230, 165, 20)]
        frames = [background.copy()]
        boxes = []
        for index, color in enumerate(colors):
            frame = background.copy()
            box = (30 + index * 45, 80, 42 + index * 45, 92)
            frame.paste(color, box)
            boxes.append(box)
            frames.append(frame)
        frames.append(background.copy())
        decoded, delays = self.encode(frames, [50] * len(frames))
        self.assertEqual(delays, [50] * len(frames))
        for index, (color, box) in enumerate(zip(colors, boxes), 1):
            pixel = decoded[index].getpixel((box[0] + 6, box[1] + 6))
            self.assertLess(max(abs(a - b) for a, b in zip(pixel, color)), 30)
            if index > 1:
                previous = boxes[index - 2]
                point = (previous[0] + 6, previous[1] + 6)
                self.assertEqual(
                    decoded[index].getpixel(point), decoded[0].getpixel(point)
                )
        self.assertEqual(decoded[-1].tobytes(), decoded[0].tobytes())

    def test_grayscale_fallback_preserves_identical_frame_duration(self):
        frame = Image.new("RGB", (80, 60), (120, 120, 120))
        decoded, delays = self.encode([frame, frame.copy()], [50, 500])
        self.assertEqual(delays, [550])
        self.assertEqual(decoded[0].getpixel((40, 30)), (120, 120, 120))


if __name__ == "__main__":
    unittest.main()
