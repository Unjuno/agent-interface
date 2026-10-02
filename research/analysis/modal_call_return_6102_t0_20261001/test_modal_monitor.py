import json
import tempfile
import unittest
from pathlib import Path

import audit
import simulate


class ModalMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = []
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "raw.jsonl"
            simulate.main(str(output))
            cls.rows = [json.loads(line) for line in output.read_text().splitlines()]

    def test_complete_corpus_matches_independent_audit(self):
        result = audit.audit_rows(self.rows)
        self.assertEqual(result["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["cases"], 14)
        self.assertEqual(result["stack_fsm_exact_matches"], 14)

    def test_flat_flag_admits_wrong_parent_continuation(self):
        row = next(r for r in self.rows if r["case_id"] == "wrong_parent_close")
        self.assertEqual(row["stack"]["decision"], "UNKNOWN_NESTING")
        self.assertEqual(row["flat"]["decision"], "ACCEPT")

    def test_unknown_and_non_lifo_controls_fail_closed(self):
        invalid = [r for r in self.rows if audit.EXPECTED[r["case_id"]] == "UNKNOWN_NESTING"]
        self.assertEqual(len(invalid), 10)
        self.assertTrue(all(r["stack"]["decision"] == "UNKNOWN_NESTING" for r in invalid))
        self.assertTrue(all(r["fsm"]["decision"] == "UNKNOWN_NESTING" for r in invalid))

    def test_auditor_rejects_stack_disposition_mutation(self):
        altered = json.loads(json.dumps(self.rows))
        altered[4]["stack"]["decision"] = "ACCEPT"
        self.assertIn("stack_mismatch:wrong_parent_close", audit.audit_rows(altered)["errors"])

    def test_auditor_rejects_event_omission(self):
        altered = json.loads(json.dumps(self.rows[:-1]))
        result = audit.audit_rows(altered)
        self.assertIn("missing_cases", result["errors"])

    def test_auditor_rejects_stale_generation_acceptance(self):
        altered = json.loads(json.dumps(self.rows))
        target = next(r for r in altered if r["case_id"] == "stale_generation_after_reuse")
        target["stack"]["decision"] = "ACCEPT"
        self.assertIn("stack_mismatch:stale_generation_after_reuse", audit.audit_rows(altered)["errors"])


if __name__ == "__main__":
    unittest.main()
