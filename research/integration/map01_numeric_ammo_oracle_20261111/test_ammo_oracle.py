import hashlib
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from ammo_oracle import (classify_ammo, verify_ammo_frame_transition,
                         verify_ammo_transition)


HERE = Path(__file__).resolve().parent
R161_TEMPLATES = HERE / "r161_frozen_templates"


class Map01AmmoOracleTests(unittest.TestCase):
    def test_r94_control_classifies_real_50_to_49_change(self):
        before = HERE / "ammo_50_template.png"
        after = HERE / "ammo_49_template.png"
        result = verify_ammo_transition(before, after, HERE)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["before"]["value"], "50")
        self.assertEqual(result["after"]["value"], "49")

    def test_r96_palette_transform_does_not_count_as_ammo_effect(self):
        before = HERE / "r96_ammo_before_50.png"
        after = HERE / "r96_ammo_after_50_palette.png"
        result = verify_ammo_transition(before, after, HERE)
        self.assertEqual(result["status"], "failure")
        self.assertEqual(result["before"]["value"], "50")
        self.assertEqual(result["after"]["value"], "50")

    def test_unknown_patch_is_not_promoted(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "unknown.png"
            Image.new("RGB", (40, 30), (127, 127, 127)).save(path)
            result = classify_ammo(path, HERE)
        self.assertEqual(result["status"], "unknown")

    def test_patch_geometry_is_exact(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "wrong-size.png"
            Image.new("RGB", (39, 30), (0, 0, 0)).save(path)
            with self.assertRaises(ValueError):
                classify_ammo(path, HERE)

    def test_full_frames_use_the_frozen_ammo_roi_for_50_to_49(self):
        with tempfile.TemporaryDirectory() as temp:
            before = Image.new("RGB", (1520, 825), (0, 0, 0))
            after = Image.new("RGB", (1520, 825), (0, 0, 0))
            with Image.open(HERE / "ammo_50_template.png") as image:
                before.paste(image, (470, 778))
            with Image.open(HERE / "ammo_49_template.png") as image:
                after.paste(image, (470, 778))
            before_path = Path(temp) / "before.png"
            after_path = Path(temp) / "after.png"
            before.save(before_path)
            after.save(after_path)

            result = verify_ammo_frame_transition(before_path, after_path, HERE)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["expected_transition"], ["50", "49"])
        self.assertEqual(result["before"]["value"], "50")
        self.assertEqual(result["after"]["value"], "49")

    def test_full_frame_geometry_mismatch_remains_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            wrong = Path(temp) / "wrong.png"
            Image.new("RGB", (40, 30), (0, 0, 0)).save(wrong)

            result = verify_ammo_frame_transition(wrong, wrong, HERE)

        self.assertEqual(result["status"], "unknown")
        self.assertEqual(result["before"]["reason"], "frame_geometry_mismatch")

    def test_full_frame_unchanged_ammo_is_not_reported_as_transition(self):
        with tempfile.TemporaryDirectory() as temp:
            frame = Image.new("RGB", (1520, 825), (0, 0, 0))
            with Image.open(HERE / "ammo_50_template.png") as image:
                frame.paste(image, (470, 778))
            before_path = Path(temp) / "before.png"
            after_path = Path(temp) / "after.png"
            frame.save(before_path)
            frame.save(after_path)

            result = verify_ammo_frame_transition(before_path, after_path, HERE)

        self.assertEqual(result["status"], "failure")
        self.assertEqual(result["before"]["value"], "50")
        self.assertEqual(result["after"]["value"], "50")

    def test_full_frame_helper_accepts_frozen_r161_templates(self):
        self.assertEqual(
            hashlib.sha256((R161_TEMPLATES / "ammo_49_template.png").read_bytes()).hexdigest(),
            "8e19d36be457c3cf5695a16e35cdd7b90a73e86e0acf3eae418edb034ea6ba99",
        )
        self.assertEqual(
            hashlib.sha256((R161_TEMPLATES / "ammo_50_template.png").read_bytes()).hexdigest(),
            "8737d02055739f3ee1f8bdac8fe842c9410ff0fb3cb8880c67676fd7323bde0d",
        )
        with tempfile.TemporaryDirectory() as temp:
            before = Image.new("RGB", (1520, 825), (0, 0, 0))
            after = Image.new("RGB", (1520, 825), (0, 0, 0))
            with Image.open(R161_TEMPLATES / "ammo_50_template.png") as image:
                before.paste(image, (470, 778))
            with Image.open(R161_TEMPLATES / "ammo_49_template.png") as image:
                after.paste(image, (470, 778))
            before_path = Path(temp) / "before.png"
            after_path = Path(temp) / "after.png"
            before.save(before_path)
            after.save(after_path)

            result = verify_ammo_frame_transition(
                before_path, after_path, R161_TEMPLATES)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["expected_transition"], ["50", "49"])


if __name__ == "__main__":
    unittest.main()
