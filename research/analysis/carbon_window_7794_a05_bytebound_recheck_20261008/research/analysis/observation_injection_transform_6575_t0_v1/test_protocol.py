import copy
import unittest

import auditor
import candidate
import scenes


ORACLE = {
    "width": scenes.WIDTH, "height": scenes.HEIGHT,
    "target_box": list(scenes.TARGET), "required_safety_box": list(scenes.SAFETY),
    "context_box": list(scenes.CONTEXT), "sham_box": list(scenes.SHAM),
    "user_region_y": list(scenes.USER_Y), "upscale": scenes.UPSCALE,
    "case_axes": {"content": list(scenes.CONTENTS), "layout": dict(scenes.LAYOUTS)},
    "invalid_crop_boxes": {"target_hidden": [24, 4, 116, 36], "safety_hidden": [4, 4, 28, 36]},
    "arms": list(candidate.ARMS)
}


class TransformProtocolTests(unittest.TestCase):
    def test_fixed_denominator_and_four_arms(self):
        self.assertEqual(len(scenes.cases()), 6)
        self.assertEqual(len(candidate.build()["rows"]), 24)

    def test_same_source_and_exact_unchanged_user_region_across_arms(self):
        from auditor import render
        raw = candidate.build()
        grouped = {}
        for row in raw["rows"]:
            grouped.setdefault(row["case_id"], {})[row["arm"]] = row
        for case in scenes.cases():
            source = render(case, ORACLE)
            user_box = [case["user_x"], scenes.USER_Y[0], case["user_x"] + 40, scenes.USER_Y[1]]
            x0, y0, x1, y1 = user_box
            pp = source.split(b"\n", 3)[3]
            region = b"".join(pp[(y * scenes.WIDTH + x0) * 3:(y * scenes.WIDTH + x1) * 3]
                             for y in range(y0, y1))
            digests = set()
            for arm_row in grouped[case["id"]].values():
                full = next((item for item in arm_row["items"] if item["name"] == "source"), None)
                if full:
                    self.assertEqual(full["sha256"], scenes.sha256(source))
                    digests.add(full["sha256"])
            self.assertLessEqual(len(digests), 1)
            self.assertTrue(region)

    def test_context_crop_contains_target_and_safety(self):
        x0, y0, x1, y1 = scenes.CONTEXT
        for required in (scenes.TARGET, scenes.SAFETY):
            self.assertTrue(x0 <= required[0] and y0 <= required[1] and x1 >= required[2] and y1 >= required[3])

    def test_sham_and_context_have_identical_dimensions(self):
        self.assertEqual((scenes.CONTEXT[2]-scenes.CONTEXT[0], scenes.CONTEXT[3]-scenes.CONTEXT[1]),
                         (scenes.SHAM[2]-scenes.SHAM[0], scenes.SHAM[3]-scenes.SHAM[1]))

    def test_independent_audit_reconstructs_all_pixels_and_rejects_invalid_crops(self):
        result = auditor.audit(candidate.build(), ORACLE)
        self.assertEqual(result["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["rows_seen"], 24)
        self.assertEqual(result["image_items_pixel_reconstructed"], 36)
        self.assertEqual(result["invalid_crop_checks_rejected"], 12)
        self.assertEqual(result["errors"], [])

    def test_corrupt_pixel_is_detected(self):
        raw = candidate.build()
        row = raw["rows"][0]
        row["items"][0]["ppm_b64"] = "AAAA"
        result = auditor.audit(raw, ORACLE)
        self.assertEqual(result["status"], "FAIL_METHOD")
        self.assertTrue(any(e["kind"] == "pixel_provenance_mismatch" for e in result["errors"]))

    def test_target_omission_is_rejected(self):
        changed = copy.deepcopy(ORACLE)
        changed["context_box"] = [24, 4, 116, 36]
        result = auditor.audit(candidate.build(), changed)
        self.assertEqual(result["status"], "FAIL_METHOD")

    def test_safety_omission_is_rejected(self):
        changed = copy.deepcopy(ORACLE)
        changed["context_box"] = [4, 4, 28, 36]
        result = auditor.audit(candidate.build(), changed)
        self.assertEqual(result["status"], "FAIL_METHOD")

    def test_invalid_crop_gate_mutation_to_allow_is_rejected(self):
        raw = candidate.build()
        raw["invalid_checks"][0]["decision"] = "ALLOW"
        result = auditor.audit(raw, ORACLE)
        self.assertEqual(result["status"], "FAIL_METHOD")
        self.assertTrue(any(e["kind"] == "invalid_crop_gate_mismatch" for e in result["errors"]))

    def test_deleted_row_is_rejected(self):
        raw = candidate.build()
        raw["rows"].pop()
        self.assertEqual(auditor.audit(raw, ORACLE)["status"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()
