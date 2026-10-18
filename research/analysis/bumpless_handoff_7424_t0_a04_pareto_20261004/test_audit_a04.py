"""Saved-output corruption and decision-gate controls for A04."""
import copy
import json
import unittest
from pathlib import Path

from audit_a04 import audit

RAW=json.loads((Path(__file__).parent/"raw.json").read_text(encoding="utf-8"))


class ParetoBoundAuditTests(unittest.TestCase):
    def test_frozen_raw_audits(self):
        result=audit(copy.deepcopy(RAW))
        self.assertTrue(result["pass"],result["errors"])
        self.assertEqual(result["classification"],"FEASIBILITY_COUNTEREXAMPLE_SCOPED")

    def test_mutated_oracle_first_action_is_rejected(self):
        raw=copy.deepcopy(RAW); raw["cases"][0]["oracle_commands"][0]=0.8
        self.assertIn("no-disturbance:first_jump_optimal_bound",audit(raw)["errors"])

    def test_mutated_tracking_metric_is_rejected(self):
        raw=copy.deepcopy(RAW); raw["cases"][0]["oracle_iae"]=0.0
        self.assertIn("no-disturbance:oracle_iae_recompute",audit(raw)["errors"])

    def test_rate_limit_violation_is_rejected(self):
        raw=copy.deepcopy(RAW); raw["cases"][0]["oracle_commands"][1]=1.0
        self.assertIn("no-disturbance:slew_bound",audit(raw)["errors"])

    def test_cold_comparator_must_match_pinned_a03_trace(self):
        raw=copy.deepcopy(RAW); raw["cases"][0]["cold_commands"][0]=0.75
        self.assertIn("no-disturbance:predecessor_cold_command_match",audit(raw)["errors"])


if __name__=="__main__":
    unittest.main(verbosity=2)
