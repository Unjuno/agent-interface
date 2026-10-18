import json
import tempfile
import unittest
from pathlib import Path

from audit import ONE_HOLD, SOURCE
from audit_v2 import audit_v2
from test_audit import REPO, copy_sources


class V16FullmainAuditV2Tests(unittest.TestCase):
    def test_missing_terminal_is_hold_not_lifecycle_pass(self):
        result = audit_v2(REPO)
        self.assertEqual(result["audit"], "HOLD_LIFECYCLE_TERMINAL_UNOBSERVED")
        self.assertEqual(result["audit_v1"], "PASS_SCOPED_V16_LIFECYCLE")
        self.assertEqual(result["v2_checks"]["construction02_terminal_rows"], 0)
        self.assertEqual(result["holds"], ["construction02_terminal_lifecycle_unobserved"])
        self.assertEqual(result["errors"], [])

    def test_down_operation_in_nested_receipt_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = copy_sources(Path(tmp))
            path = copy / ONE_HOLD / "out/session/events.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
            transition = next(row for row in rows if row.get("event") == "input_release_transition")
            transition["owner_thread_keyup_receipt"]["operation"] = "down"
            path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            result = audit_v2(copy)
        self.assertEqual(result["audit"], "FAIL_V16_LIFECYCLE_AUDIT")
        self.assertIn("one_hold_nested_keyup_semantics_mismatch", result["errors"])

    def test_false_sync_in_nested_receipt_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = copy_sources(Path(tmp))
            path = copy / ONE_HOLD / "out/session/events.jsonl"
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
            transition = next(row for row in rows if row.get("event") == "input_release_transition")
            transition["owner_thread_keyup_receipt"]["server_sync_completed"] = False
            path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            result = audit_v2(copy)
        self.assertIn("one_hold_nested_keyup_semantics_mismatch", result["errors"])

    def test_empty_owner_sample_before_release_transition_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = copy_sources(Path(tmp))
            path = copy / ONE_HOLD / "out/session/owner-events.json"
            rows = json.loads(path.read_text(encoding="utf-8"))
            empty = next(row for row in rows if row.get("event") == "owner_release" and row.get("reason") == "release")
            empty["verified_ns"] = 1
            path.write_text(json.dumps(rows), encoding="utf-8")
            result = audit_v2(copy)
        self.assertIn("one_hold_empty_release_not_after_keyup_transition", result["errors"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
