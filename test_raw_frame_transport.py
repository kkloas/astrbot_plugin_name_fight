"""Verify lossless patch reconstruction and GIF parity with the PNG path."""

import base64
import struct
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image
from web_battle_renderer import _apply_frame_patch, _read_frame, _write_gif


def packet(frame, x=0, y=0, box=None):
    patch = frame.crop(box) if box else frame
    return {
        "width": frame.width,
        "height": frame.height,
        "x": x,
        "y": y,
        "patchWidth": patch.width,
        "patchHeight": patch.height,
        "data": base64.b64encode(patch.convert("RGBA").tobytes()).decode("ascii"),
    }


class RawFrameTransportTests(unittest.TestCase):
    def test_patch_replaces_pixels_and_empty_patch_preserves_them(self):
        first = Image.new("RGBA", (80, 60), (120, 120, 120, 255))
        second = first.copy()
        second.paste((235, 30, 60, 255), (7, 9, 23, 27))
        canvas = _apply_frame_patch(None, packet(first))
        canvas = _apply_frame_patch(canvas, packet(second, 7, 9, (7, 9, 23, 27)))
        self.assertEqual(canvas.tobytes(), second.tobytes())
        empty = dict(packet(first), patchWidth=0, patchHeight=0, data="")
        self.assertIs(_apply_frame_patch(canvas, empty), canvas)
        self.assertEqual(canvas.tobytes(), second.tobytes())
        canvas = _apply_frame_patch(canvas, packet(first, 7, 9, (7, 9, 23, 27)))
        self.assertEqual(canvas.tobytes(), first.tobytes())

    def test_invalid_patch_cannot_corrupt_previous_frame(self):
        canvas = Image.new("RGBA", (80, 60), "white")
        original = canvas.tobytes()
        valid = packet(canvas)
        for changes in (
            {"data": ""},
            {"data": "!"},
            {"x": 1},
            {"width": 721},
            {"height": 2049},
            {"patchWidth": 0},
            {"width": 80.0},
            {"x": -1},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                _apply_frame_patch(canvas, dict(valid, **changes))
            self.assertEqual(canvas.tobytes(), original)
        with self.assertRaises(ValueError):
            _apply_frame_patch(None, packet(canvas, 7, 9, (7, 9, 23, 27)))

    def test_raw_and_png_produce_identical_gifs_including_variable_heights(self):
        first = Image.new("RGBA", (80, 60), "gray")
        second = first.copy()
        second.paste("red", (20, 10, 40, 30))
        third = Image.new("RGBA", (80, 72), "white")
        third.paste(second, (0, 0))
        frames = [first, second, second, first, third]
        outputs = []
        with tempfile.TemporaryDirectory() as directory:
            for raw in (False, True):
                with BytesIO() as spool:
                    offsets = []
                    for frame in frames:
                        start = spool.tell()
                        if raw:
                            spool.write(b"NFR1" + struct.pack("<II", *frame.size))
                            spool.write(frame.tobytes())
                        else:
                            frame.save(spool, "PNG")
                        offsets.append((start, spool.tell() - start))
                    path = Path(directory) / f"{raw}.gif"
                    _write_gif(spool, offsets, [50, 50, 50, 50, 500], path)
                    outputs.append(path.read_bytes())
            self.assertEqual(*outputs)

    def test_truncated_raw_frame_is_rejected(self):
        for data in (b"NFR1", b"NFR1" + struct.pack("<II", 80, 60) + b"\0"):
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                _read_frame(BytesIO(data), (0, len(data)))


if __name__ == "__main__":
    unittest.main()
