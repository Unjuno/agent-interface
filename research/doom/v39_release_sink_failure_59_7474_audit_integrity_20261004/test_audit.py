"""Corruption controls prove that trace omissions and summary drift fail closed."""
import copy
import json
import unittest
from pathlib import Path

from audit import audit

RAW = json.loads((Path(__file__).parent / "predecessor-raw.json").read_text(encoding="utf-8"))


class AuditIntegrityTests(unittest.TestCase):
    def test_pr7486_saved_case_summary_passes_with_consistent_trace(self):
        self.assertTrue(audit(copy.deepcopy(RAW))["pass"])

    def test_missing_attempt_trace_fails(self):
        raw = copy.deepcopy(RAW)
        raw["rows"][1]["attempts"] = []
        self.assertFalse(audit(raw)["pass"])

    def test_sink_call_count_must_match_trace(self):
        raw = copy.deepcopy(RAW)
        raw["rows"][1]["sink_calls"] = 0
        self.assertIn("fail_before_accept:sink_calls_trace_mismatch", audit(raw)["errors"])

    def test_retry_summary_must_match_second_attempt(self):
        raw = copy.deepcopy(RAW)
        raw["rows"][1]["retry_suppressed"] = False
        self.assertIn("fail_before_accept:retry_summary_mismatch", audit(raw)["errors"])

    def test_duplicate_case_cannot_overwrite_original(self):
        raw = copy.deepcopy(RAW)
        raw["rows"].append(copy.deepcopy(raw["rows"][0]))
        self.assertFalse(audit(raw)["pass"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
