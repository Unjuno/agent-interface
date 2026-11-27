"""Local deterministic controls for the p07 independent synthetic application."""

import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from Xlib import X

from research.integration.current_main_appserver_public_mcp_visual_grounding_20261025_p07.fake_factory import (
    EFFECT_PIXEL, GREEN_RECT, GroundingFakeX, SUCCESS_RGB, _Cleanup,
)


class GroundingFakeXTests(unittest.TestCase):
    def test_only_green_target_click_commits_the_effect_pixel(self):
        with tempfile.TemporaryDirectory() as temp:
            cleanup = _Cleanup()
            self.addCleanup(cleanup.doCleanups)
            fake = GroundingFakeX(cleanup, temp)
            fake.emit(None, X.MotionNotify, 0, x=7, y=8)
            fake.emit(None, X.ButtonPress, 1)
            wrong_pixel = list(Image.frombytes(
                "RGB", (32, 32), fake.raw, "raw", "BGRX").getpixel(EFFECT_PIXEL))
            self.assertNotEqual(wrong_pixel, SUCCESS_RGB)
            fake.emit(None, X.MotionNotify, 0, x=16, y=8)
            fake.emit(None, X.ButtonPress, 1)
            right_pixel = list(Image.frombytes(
                "RGB", (32, 32), fake.raw, "raw", "BGRX").getpixel(EFFECT_PIXEL))
            self.assertEqual(right_pixel, list(SUCCESS_RGB))
            self.assertEqual(len(fake.button_events), 2)
            row = json.loads((Path(temp) / "synthetic-effect-receipt.json").read_text())
            self.assertEqual(row["click_point"], [16, 8])
            self.assertEqual(row["button_press_count"], 2)

    def test_input_screenshot_has_the_preregistered_green_target(self):
        cleanup = _Cleanup()
        self.addCleanup(cleanup.doCleanups)
        fake = GroundingFakeX(cleanup, tempfile.gettempdir())
        image = Image.frombytes("RGB", (32, 32), fake.raw, "raw", "BGRX")
        self.assertEqual(image.getpixel((18, 12)), (0, 220, 40))
        self.assertEqual(GREEN_RECT, (12, 3, 20, 13))


if __name__ == "__main__":
    unittest.main()
