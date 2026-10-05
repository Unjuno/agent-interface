"""Offline checks for exact-token matching and the native Windows OCR worker."""

import os
import tempfile
import unittest
from pathlib import Path

from research.live_control.windows_ocr_observer_v1 import (
    WindowsOcrObserver,
    exact_token_present,
    exact_token_state,
)


class ExactTokenTests(unittest.TestCase):
    def test_match_requires_the_complete_token(self):
        self.assertTrue(exact_token_present("Value: t991025-1", "t991025-1"))
        self.assertFalse(exact_token_present("Value: xt991025-1", "t991025-1"))
        self.assertFalse(exact_token_present("Value: t991025-10", "t991025-1"))
        self.assertFalse(exact_token_present("Value: t991025-2", "t991025-1"))
        self.assertEqual(exact_token_state("", "t991025-1"), "unknown")
        self.assertFalse(exact_token_state("Value: t991025-2", "t991025-1"))

    def test_invalid_expected_token_is_rejected(self):
        for token in ("", 7, None):
            with self.subTest(token=token):
                with self.assertRaises(ValueError):
                    exact_token_present("text", token)
                with self.assertRaises(ValueError):
                    exact_token_state("", token)


@unittest.skipUnless(os.name == "nt", "native OCR integration requires Windows")
class NativeOcrTests(unittest.TestCase):
    def test_persistent_worker_reads_exact_ascii_token_and_negative_control(self):
        from PIL import Image, ImageDraw, ImageFont

        with tempfile.TemporaryDirectory(prefix="interface-ocr-") as directory:
            image_path = Path(directory) / "token.png"
            image = Image.new("RGB", (640, 240), "white")
            draw = ImageDraw.Draw(image)
            font_path = Path(os.environ["WINDIR"]) / "Fonts" / "arial.ttf"
            draw.text((30, 40), "Enter token: t991025-1",
                      font=ImageFont.truetype(str(font_path), 36), fill="black")
            image.save(image_path)

            with WindowsOcrObserver() as observer:
                first = observer.recognize(image_path)
                second = observer.recognize(image_path)

            self.assertEqual(first["status"], "ok")
            self.assertTrue(exact_token_present(first["text"], "t991025-1"))
            self.assertFalse(exact_token_present(first["text"], "t991025-2"))
            self.assertEqual(first["language"], second["language"])
            self.assertTrue(first["text"])
            self.assertGreater(first["elapsed_ns"], 0)


if __name__ == "__main__":
    unittest.main()
