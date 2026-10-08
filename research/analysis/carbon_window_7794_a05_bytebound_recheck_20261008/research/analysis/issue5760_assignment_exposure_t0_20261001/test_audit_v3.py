"""Pre-formal constructor tests; no candidate, oracle, or formal raw audit calls."""
import copy
import json
import unittest
from pathlib import Path

import audit_v3

ROOT = Path(__file__).resolve().parent


class AuditV3Construction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "fixtures.json").read_text(encoding="utf-8"))
        cls.freeze = json.loads((ROOT / "FREEZE_AUDIT_V3.json").read_text(encoding="utf-8"))

    def test_exact_selection_reversal(self):
        self.assertEqual(audit_v3.summarize(self.data["cases"][0]), audit_v3.EXPECTED["selection_reversal"])

    def test_exact_null_control(self):
        self.assertEqual(audit_v3.summarize(self.data["cases"][1]), audit_v3.EXPECTED["null_balanced_exposure"])

    def test_drop_fallback_denominator_rejected(self):
        case = copy.deepcopy(self.data["cases"][0])
        case["rows"] = [row for row in case["rows"] if row["A_path"] != "fallback"]
        self.assertTrue(audit_v3.rejects_mutation(case))

    def test_relabel_fallback_rejected(self):
        case = copy.deepcopy(self.data["cases"][0])
        for row in case["rows"]:
            if row["A_path"] == "fallback":
                row["A_path"] = "local"
        self.assertTrue(audit_v3.rejects_mutation(case))

    def test_zero_fallback_time_rejected(self):
        case = copy.deepcopy(self.data["cases"][0])
        for row in case["rows"]:
            if row["A_path"] == "fallback":
                row["A_total_time"] = 0
        self.assertTrue(audit_v3.rejects_mutation(case))

    def test_freeze_names_audit_allocation(self):
        self.assertTrue(self.freeze["audit_allocation"])
        self.assertEqual(self.freeze["candidate_oracle_invocations_v3"], 0)
        self.assertEqual(self.freeze["audit_v3_invocations"], 1)

    def test_v2_stop_is_recorded(self):
        record = json.loads((ROOT / "AUDIT_V2_EXECUTION.json").read_text(encoding="utf-8"))
        self.assertEqual(record["disposition"], "STOP_AUDIT_V2_CONFIGURATION_MISMATCH")


if __name__ == "__main__":
    unittest.main(verbosity=2)
