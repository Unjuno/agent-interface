from pathlib import Path
import tempfile
import unittest

from PIL import Image

from ammo_oracle import classify_ammo, verify_ammo_transition


HERE = Path(__file__).resolve().parent


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


if __name__ == "__main__":
    unittest.main()
