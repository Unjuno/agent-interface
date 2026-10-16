import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from research.live_control.inkscape_red_target_planner_v1 import prepare, validate


class InkscapeRedTargetPlannerTests(unittest.TestCase):
    def image(self, path, box=(20, 30, 50, 60)):
        image = Image.new("RGB", (100, 100), "white")
        ImageDraw.Draw(image).rectangle(box, fill=(255, 0, 0))
        image.save(path)

    def test_prepares_exact_center_and_validates_fresh_target(self):
        with tempfile.TemporaryDirectory() as directory:
            first, fresh = Path(directory) / "a.png", Path(directory) / "b.png"
            self.image(first); self.image(fresh)
            plan = prepare(first, [10, 20, 70, 80])
            self.assertEqual(plan["target"]["bbox"], [20, 30, 51, 61])
            self.assertEqual(plan["action"]["x"], 35)
            result = validate(plan, fresh)
            self.assertEqual(result["status"], "VALID_CURRENT")
            self.assertFalse(result["grants_input_authority"])

    def test_changed_target_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            first, fresh = Path(directory) / "a.png", Path(directory) / "b.png"
            self.image(first); self.image(fresh, (25, 30, 55, 60))
            result = validate(prepare(first, [10, 20, 70, 80]), fresh)
            self.assertEqual(result["status"], "REJECTED_TARGET_CHANGED")
            self.assertFalse(result["action_may_proceed_to_admission"])

    def test_non_rectangular_or_missing_target_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "a.png"
            Image.new("RGB", (100, 100), "white").save(path)
            with self.assertRaises(ValueError): prepare(path, [0, 0, 100, 100])


if __name__ == "__main__": unittest.main()
