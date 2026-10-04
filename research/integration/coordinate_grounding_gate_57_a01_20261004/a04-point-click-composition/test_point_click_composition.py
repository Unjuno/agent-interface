from __future__ import annotations

import unittest

try:
    from candidate import run_composition
except ModuleNotFoundError:
    run_composition = None


class PointClickCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if run_composition is None:
            raise AssertionError("point-click composition has not been implemented")
        cls.result = run_composition()

    def test_five_retained_proposals_preserve_source_identity_to_action_spec(self):
        cases = self.result["cases"]
        self.assertEqual(len(cases), 5)
        for case in cases:
            with self.subTest(task=case["task"]):
                self.assertEqual(case["mint"]["status"], "VALID")
                self.assertTrue(case["resolution"]["eligible"])
                self.assertEqual(case["resolution"]["status"], "VALID")
                self.assertEqual(case["action_spec"]["target_handle"], case["alias"])
                self.assertEqual(case["action_spec"]["offset"], case["offset"])
                self.assertEqual(case["action_spec"]["point"], case["proposal_point"])
                self.assertEqual(case["action_spec"]["box"], case["box"])
                self.assertEqual(case["action_spec"]["patch_sha256"], case["patch_sha256"])

    def test_fixed_offset_and_wrong_alias_are_rejected_before_action_spec(self):
        negative = self.result["negative_cases"]
        self.assertFalse(negative["fixed_offset"]["accepted"])
        self.assertEqual(negative["fixed_offset"]["action_specs"], [])
        self.assertFalse(negative["wrong_alias"]["accepted"])
        self.assertEqual(negative["wrong_alias"]["action_specs"], [])

    def test_changed_patch_focus_surface_and_stale_observation_never_reach_sink(self):
        expected = {"changed_patch": ("fresh_patch_check", "MISSING"),
                    "focus_changed": ("fresh_resolution", "SCOPE_MISMATCH"),
                    "surface_changed": ("fresh_resolution", "SCOPE_MISMATCH"),
                    "stale": ("fresh_resolution", "STALE")}
        for name, case in self.result["ineligible_cases"].items():
            with self.subTest(case=name):
                self.assertFalse(case["accepted"])
                self.assertEqual(case["action_specs"], [])
                self.assertEqual((case["stage"], case["status"]), expected[name])

    def test_run_is_inert(self):
        self.assertEqual(self.result["input_dispatch_count"], 0)
        self.assertEqual(self.result["gui_call_count"], 0)
        self.assertEqual(self.result["model_call_count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
