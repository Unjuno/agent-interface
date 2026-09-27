import json
import unittest
from copy import deepcopy
from pathlib import Path

from audit import audit_data
from reanalyze import expected

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "confidence_trajectory_4588_v1/results/formal-01/raw.jsonl"
RESULT = HERE / "results/formal-01/reanalysis/reanalysis.json"


class FrozenRuleTests(unittest.TestCase):
    def test_falling_high_confidence_retains_current_only_positive(self):
        case = {"current_valid": True, "state": "ACTION_REQUIRED", "history_status": "VALID", "scores": [0.94, 0.87, 0.77], "times_ms": [0, 100, 200]}
        self.assertEqual(expected(case, "CURRENT_ONLY"), "ACTION")
        self.assertEqual(expected(case, "LEVEL_PLUS_VELOCITY"), "ACTION")


class RawAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_bytes = RAW.read_bytes()
        cls.result = json.loads(RESULT.read_text())

    def test_reconstructs_unmodified_formal_output_from_raw(self):
        self.assertEqual(audit_data(self.raw_bytes, self.result), [])

    def test_rejects_reversed_changed_decisions(self):
        altered = deepcopy(self.result)
        altered["changed_velocity_rows"][0]["predecessor"], altered["changed_velocity_rows"][0]["frozen_spec"] = "ACTION", "YIELD"
        self.assertIn("changed_rows_reconstruction", audit_data(self.raw_bytes, altered))

    def test_rejects_unrelated_input_hash(self):
        altered = deepcopy(self.result)
        altered["input_sha256"] = "0" * 64
        self.assertIn("input_sha256", audit_data(self.raw_bytes, altered))

    def test_low_confidence_rising_rescue(self):
        case = {"current_valid": True, "state": "ACTION_REQUIRED", "history_status": "VALID", "scores": [0.14, 0.32, 0.60], "times_ms": [0, 100, 200]}
        self.assertEqual(expected(case, "LEVEL_PLUS_VELOCITY"), "ACTION")

    def test_invalid_history_falls_back(self):
        case = {"current_valid": True, "state": "ACTION_REQUIRED", "history_status": "STALE_PREVIOUS", "scores": [0.55, 0.72, 0.95], "times_ms": [0, 100, 200]}
        self.assertEqual(expected(case, "LEVEL_PLUS_VELOCITY"), "ACTION")


if __name__ == "__main__":
    unittest.main()
