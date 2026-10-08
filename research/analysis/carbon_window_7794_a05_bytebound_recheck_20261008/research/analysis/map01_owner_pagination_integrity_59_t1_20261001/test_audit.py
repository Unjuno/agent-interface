import json
import tempfile
import unittest
from pathlib import Path

from audit import audit


class AuditTests(unittest.TestCase):
    def test_exact_candidate_evidence_passes_and_detects_gap(self):
        raw = {
            "case_count": 1,
            "counterexample_count": 1,
            "decision": "PASS_BOUNDED_FAIL_CLOSED_GAP_FOUND",
            "cases": [{
                "full_run_ids": [1, 2],
                "visible_run_ids": [2],
                "current_run_id": 2,
                "api_total_count": 1,
                "incomplete": True,
                "helper_result": "PASS_CANONICAL_GLOBAL_OWNER",
                "helper_admitted": True,
                "oracle_admitted": False,
            }],
            "counterexamples": [],
        }
        raw["counterexamples"] = [raw["cases"][0]]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            result = audit(path)
        self.assertTrue(result["passed"])
        self.assertEqual(result["counterexample_count"], 1)

    def test_corrupt_oracle_classification_is_rejected(self):
        raw = {
            "case_count": 1,
            "counterexample_count": 0,
            "decision": "HOLD_NO_GAP_IN_BOUNDED_MODEL",
            "cases": [{
                "full_run_ids": [1, 2],
                "visible_run_ids": [2],
                "current_run_id": 2,
                "api_total_count": 1,
                "incomplete": False,
                "helper_result": "PASS_CANONICAL_GLOBAL_OWNER",
                "helper_admitted": True,
                "oracle_admitted": True,
            }],
            "counterexamples": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            result = audit(path)
        self.assertFalse(result["passed"])
        self.assertIn("independent_oracle_disagreement", result["errors"])


if __name__ == "__main__":
    unittest.main()
