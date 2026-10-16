import unittest

from research.live_control.post_model_target_revalidation_v1 import receipt


class PostModelTargetRevalidationTests(unittest.TestCase):
    def fixtures(self):
        binding = {"focus": 10, "surface": 10, "geometry": [0, 0, 100, 100]}
        source = {"sequence": 2, "capture_ns": 100, "pointer_binding": binding, "exact": True}
        current = {"sequence": 3, "capture_ns": 200, "pointer_binding": binding, "exact": True}
        mint = {"status": "VALID", "handle": "h", "patch_sha256": "abc"}
        resolution = {"eligible": True, "status": "VALID", "handle": "h",
                      "patch_sha256": "abc", "sequence": 3, "point": [10, 20]}
        return mint, resolution, source, current

    def test_binds_later_current_patch_without_authority(self):
        result = receipt(*self.fixtures(), "call-1")
        self.assertEqual(result["status"], "CURRENT_PATCH_MATCH_NO_AUTHORITY")
        self.assertEqual(result["model_source_sequence"], 2)
        self.assertEqual(result["current_sequence"], 3)
        self.assertFalse(result["grants_semantic_authority"])
        self.assertFalse(result["grants_input_authority"])

    def test_same_sequence_is_rejected(self):
        mint, resolution, source, current = self.fixtures()
        current["sequence"] = source["sequence"]
        resolution["sequence"] = source["sequence"]
        with self.assertRaisesRegex(ValueError, "strictly later"):
            receipt(mint, resolution, source, current, "call-1")

    def test_binding_change_is_rejected(self):
        mint, resolution, source, current = self.fixtures()
        current["pointer_binding"] = {**current["pointer_binding"], "surface": 11}
        with self.assertRaisesRegex(ValueError, "unchanged current binding"):
            receipt(mint, resolution, source, current, "call-1")

    def test_patch_change_is_rejected(self):
        mint, resolution, source, current = self.fixtures()
        resolution["patch_sha256"] = "other"
        with self.assertRaisesRegex(ValueError, "matching current"):
            receipt(mint, resolution, source, current, "call-1")


if __name__ == "__main__":
    unittest.main()
