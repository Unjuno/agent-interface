import unittest
from PIL import Image, ImageDraw
from pairwise_probe import compare_pair


class PairwiseProbeTests(unittest.TestCase):
    def make_image(self, health_patch, outside_change=False):
        image = Image.new("RGB", (640, 700), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((440, 585, 535, 635), fill=health_patch)
        if outside_change:
            draw.rectangle((20, 20, 100, 100), fill=(255, 255, 255))
        return image

    def test_equal_health_label_ignores_changes_outside_roi(self):
        before = self.make_image((80, 0, 0))
        after = self.make_image((80, 0, 0), outside_change=True)
        row = compare_pair(before, after, expected_health_changed=False)
        self.assertEqual(row["status"], "UNCHANGED")

    def test_changed_health_label_invalidates(self):
        before = self.make_image((80, 0, 0))
        after = self.make_image((0, 80, 0))
        row = compare_pair(before, after, expected_health_changed=True)
        self.assertEqual(row["status"], "INVALIDATED")

    def test_reported_label_must_match_guard_outcome(self):
        before = self.make_image((80, 0, 0))
        after = self.make_image((80, 0, 0))
        with self.assertRaises(AssertionError):
            compare_pair(before, after, expected_health_changed=True)


if __name__ == "__main__":
    unittest.main()
