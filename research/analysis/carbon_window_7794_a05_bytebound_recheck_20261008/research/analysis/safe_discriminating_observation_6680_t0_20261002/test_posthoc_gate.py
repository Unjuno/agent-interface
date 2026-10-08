import copy
import json
import unittest
from pathlib import Path

import posthoc_gate


ROOT = Path(__file__).parent


class PosthocGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / "temporal_fixture.json").read_text())
        cls.oracle = json.loads((ROOT / "temporal_oracle.json").read_text())
        cls.raw = json.loads((ROOT / "temporal_v4_construction.raw.json").read_text())
        cls.audit = json.loads((ROOT / "temporal_v4_construction.audit.json").read_text())

    def test_gate_adjudication_rejects_v2_ineligible_fixed_reobservations(self):
        raw = json.loads((ROOT / "temporal_v2_construction.raw.json").read_text())
        audit = json.loads((ROOT / "temporal_v2_construction.audit.json").read_text())
        result = posthoc_gate.adjudicate(raw, self.fixture, self.oracle, audit)
        self.assertEqual(result["status"], "FAIL_PREREGISTERED_GATE")
        self.assertTrue(any("fixed reobserve arm" in e for e in result["errors"]))
        self.assertEqual(result["coverage_rows"], 20)

    def test_gate_adjudication_rejects_v3_probe_on_nondiscriminating_alarm(self):
        raw = json.loads((ROOT / "temporal_v3_construction.raw.json").read_text())
        audit = json.loads((ROOT / "temporal_v3_construction.audit.json").read_text())
        result = posthoc_gate.adjudicate(raw, self.fixture, self.oracle, audit)
        self.assertEqual(result["status"], "FAIL_PREREGISTERED_GATE")
        self.assertTrue(any("discriminating prior" in e for e in result["errors"]))

    def test_frozen_v4_construction_meets_all_declared_gates(self):
        result = posthoc_gate.adjudicate(self.raw, self.fixture, self.oracle, self.audit)
        self.assertEqual(result["status"], "PASS_PREREGISTERED_GATES_CONSTRUCTION_ONLY")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["coverage_rows"], 20)

    def test_d_gate_failure_overrides_green_audit_receipt(self):
        raw = copy.deepcopy(self.raw)
        row = next(r for r in raw["rows"] if r["case_id"] == "c01" and r["policy"] == "bounded_diagnose")
        row["action"] = "reset"
        result = posthoc_gate.adjudicate(raw, self.fixture, self.oracle, self.audit)
        self.assertEqual(self.audit["status"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["status"], "FAIL_PREREGISTERED_GATE")

    def test_fixed_policy_arm_cannot_be_silently_relabelled(self):
        raw = copy.deepcopy(self.raw)
        row = next(r for r in raw["rows"] if r["case_id"] == "c01" and r["policy"] == "always_reset")
        row["action"] = "yield"
        result = posthoc_gate.adjudicate(raw, self.fixture, self.oracle, self.audit)
        self.assertEqual(result["status"], "FAIL_PREREGISTERED_GATE")
        self.assertTrue(any("fixed reset arm" in e for e in result["errors"]))

    def test_coverage_gap_fails_even_with_original_audit_receipt(self):
        raw = copy.deepcopy(self.raw)
        raw["rows"].pop()
        result = posthoc_gate.adjudicate(raw, self.fixture, self.oracle, self.audit)
        self.assertEqual(result["status"], "FAIL_PREREGISTERED_GATE")
        self.assertTrue(any("coverage" in e for e in result["errors"]))

    def test_post_recovery_recurrence_gate_is_recomputed(self):
        oracle = copy.deepcopy(self.oracle)
        oracle["worlds"]["c01"]["effects"]["reobserve"]["post_recovery_residual"] = 2
        result = posthoc_gate.adjudicate(self.raw, self.fixture, oracle, self.audit)
        self.assertEqual(result["status"], "FAIL_PREREGISTERED_GATE")
        self.assertTrue(any("residual recurrence" in e for e in result["errors"]))

    def test_unknown_action_is_classified_not_crashing(self):
        raw = copy.deepcopy(self.raw)
        row = next(r for r in raw["rows"] if r["case_id"] == "c01" and r["policy"] == "bounded_diagnose")
        row["action"] = "invented_action"
        result = posthoc_gate.adjudicate(raw, self.fixture, self.oracle, self.audit)
        self.assertEqual(result["status"], "FAIL_PREREGISTERED_GATE")
        self.assertTrue(any("frozen effect" in e for e in result["errors"]))


if __name__ == "__main__":
    unittest.main()
