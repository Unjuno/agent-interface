from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from auditor import audit
from candidate import evaluate


HERE = Path(__file__).parent


class ObservationOmissionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
        cls.raw = evaluate(cls.fixture)

    def test_independent_audit_reconstructs_all_five_scenarios(self):
        result = audit(self.fixture, self.raw)
        self.assertEqual(result["disposition"], "PASS_METHOD_SCOPED", result)
        self.assertEqual(len(self.raw["scenarios"]), 5)
        self.assertEqual(sum(len(s["arms"]) for s in self.raw["scenarios"]), 10)

    def test_early_omission_preserves_effect_and_reduces_calls_and_bytes(self):
        scenario = self.raw["scenarios"][0]
        baseline, omitted = scenario["arms"]
        self.assertEqual(baseline["effect"], "target_saved")
        self.assertEqual(omitted["effect"], baseline["effect"])
        self.assertFalse(omitted["regret_vs_baseline"])
        self.assertLess(omitted["model_visible_count"], baseline["model_visible_count"])
        self.assertLess(omitted["model_visible_bytes"], baseline["model_visible_bytes"])

    def test_transition_omission_has_explicit_effect_regret(self):
        scenario = self.raw["scenarios"][1]
        self.assertTrue(scenario["arms"][1]["regret_vs_baseline"])
        self.assertEqual(scenario["arms"][1]["effect"], "target_missed")

    def test_completion_boundary_excludes_later_capture_in_both_arms(self):
        scenario = self.raw["scenarios"][2]
        for arm in scenario["arms"]:
            row = next(e for e in arm["events"] if e["event_id"] == "post_completion_capture")
            self.assertFalse(row["model_visible"])
            self.assertEqual(row["counted_bytes"], 0)
        self.assertEqual(scenario["arms"][0]["model_visible_count"], scenario["arms"][1]["model_visible_count"])

    def test_capture_without_delivery_is_not_model_visibility_or_cost(self):
        scenario = self.raw["scenarios"][3]
        row = next(e for e in scenario["arms"][0]["events"] if e["event_id"] == "undelivered_cue")
        self.assertTrue(row["captured"])
        self.assertFalse(row["delivered"])
        self.assertFalse(row["model_visible"])
        self.assertEqual(row["counted_bytes"], 0)
        self.assertFalse(scenario["arms"][0]["exact_effect"])

    def test_mandatory_safety_cue_bypasses_optional_omission(self):
        scenario = self.raw["scenarios"][4]
        omitted_arm = scenario["arms"][1]
        row = next(e for e in omitted_arm["events"] if e["event_id"] == "mandatory_revoke")
        self.assertTrue(row["requested_omission"])
        self.assertFalse(row["omitted"])
        self.assertTrue(row["model_visible"])
        self.assertTrue(omitted_arm["safe_stop"])
        self.assertEqual(omitted_arm["effect"], "safe_stop")

    def test_auditor_rejects_five_mutation_controls(self):
        mutations = []

        raw = copy.deepcopy(self.raw)
        arm = raw["scenarios"][3]["arms"][0]
        row = next(e for e in arm["events"] if e["event_id"] == "undelivered_cue")
        row["model_visible"] = True
        row["counted_bytes"] = 21
        mutations.append(raw)

        raw = copy.deepcopy(self.raw)
        arm = raw["scenarios"][4]["arms"][1]
        row = next(e for e in arm["events"] if e["event_id"] == "mandatory_revoke")
        row["omitted"] = True
        row["model_visible"] = False
        row["counted_bytes"] = 0
        mutations.append(raw)

        raw = copy.deepcopy(self.raw)
        arm = raw["scenarios"][2]["arms"][0]
        row = next(e for e in arm["events"] if e["event_id"] == "post_completion_capture")
        row["model_visible"] = True
        row["counted_bytes"] = 23
        arm["model_visible_count"] += 1
        arm["model_visible_bytes"] += 23
        mutations.append(raw)

        raw = copy.deepcopy(self.raw)
        raw["scenarios"][1]["arms"][1]["exact_effect"] = True
        mutations.append(raw)

        raw = copy.deepcopy(self.raw)
        arm = raw["scenarios"][0]["arms"][0]
        row = next(e for e in arm["events"] if e["event_id"] == "decision_cue")
        row["counted_bytes"] -= 1
        arm["model_visible_bytes"] -= 1
        mutations.append(raw)

        for index, mutated in enumerate(mutations):
            with self.subTest(mutation=index):
                self.assertEqual(audit(self.fixture, mutated)["disposition"], "FAIL_METHOD")


if __name__ == "__main__":
    unittest.main()
