import unittest

from PIL import Image

from audit import COUNTER_ROI, FRAME_SIZE, digest, verify_inventory_data


class CounterPixelAuditTests(unittest.TestCase):
    def test_counter_crop_ignores_button_hover_pixels(self):
        before = Image.new("RGB", FRAME_SIZE, (244, 245, 246))
        after = before.copy()
        for y in range(70, 110):
            for x in range(10, 310):
                after.putpixel((x, y), (255, 255, 255))
        raw_before = before.convert("RGBX").tobytes()
        raw_after = after.convert("RGBX").tobytes()
        self.assertNotEqual(digest(raw_before), digest(raw_after))
        self.assertEqual(
            digest(Image.frombytes("RGBX", FRAME_SIZE, raw_before).convert("RGB").crop(COUNTER_ROI).tobytes()),
            digest(Image.frombytes("RGBX", FRAME_SIZE, raw_after).convert("RGB").crop(COUNTER_ROI).tobytes()),
        )

    def test_counter_region_pixel_mutation_changes_roi_digest(self):
        before = Image.new("RGB", FRAME_SIZE, (244, 245, 246))
        after = before.copy()
        x0, y0, _, _ = COUNTER_ROI
        after.putpixel((x0, y0), (0, 0, 0))
        self.assertNotEqual(digest(before.crop(COUNTER_ROI).tobytes()), digest(after.crop(COUNTER_ROI).tobytes()))

    def test_inventory_detects_unreferenced_artifact_tamper(self):
        expected = [
            {"path": "linked.raw", "bytes": 6, "sha256": digest(b"linked"), "git_blob": "abc"},
            {"path": "unreferenced.raw", "bytes": 9, "sha256": digest(b"auxiliary"), "git_blob": "def"},
        ]
        good = {"linked.raw": b"linked", "unreferenced.raw": b"auxiliary"}
        self.assertEqual(verify_inventory_data(expected, good), [])
        bad = {**good, "unreferenced.raw": b"tampered"}
        self.assertTrue(any("unreferenced.raw" in error for error in verify_inventory_data(expected, bad)))

    def test_inventory_detects_missing_and_unexpected_paths(self):
        expected = [{"path": "one.raw", "bytes": 3, "sha256": digest(b"one"), "git_blob": "abc"}]
        errors = verify_inventory_data(expected, {"extra.raw": b"extra"})
        self.assertTrue(any("missing input artifact: one.raw" in error for error in errors))
        self.assertTrue(any("unexpected input artifact: extra.raw" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
