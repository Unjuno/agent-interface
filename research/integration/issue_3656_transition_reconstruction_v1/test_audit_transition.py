import copy
import json
import unittest
from pathlib import Path

from audit_transition import audit

RAW_PATH = Path(__file__).parent / "evidence" / "formal-01" / "result.json"


def fixture():
    return json.loads(RAW_PATH.read_text(encoding="utf-8"))


class ReconstructionTests(unittest.TestCase):
    def test_retained_raw_holds_only_for_missing_observation_receipts(self):
        result = audit(fixture())
        self.assertEqual(result["decision"], "HOLD_AUDIT_EVIDENCE_INCOMPLETE")
        self.assertEqual(result["error_count"], 0)
        self.assertIn("Chromium old-window-absence receipt is missing", result["holds"])
        self.assertIn("active-window observation at Calc return is missing", result["holds"])
        self.assertFalse(result["runner_checks_used_as_evidence"])

    def test_extra_event_rejected(self):
        raw = fixture()
        raw["ledger"].insert(1, copy.deepcopy(raw["ledger"][1]))
        result = audit(raw)
        self.assertTrue(result["errors"] or result["holds"])
        self.assertNotEqual(result["decision"], "PASS_AUDIT_RECONSTRUCTION_SCOPED")

    def test_reordered_event_rejected(self):
        raw = fixture()
        raw["ledger"][1], raw["ledger"][2] = raw["ledger"][2], raw["ledger"][1]
        self.assertIn("sequence numbers", " ".join(audit(raw)["errors"]))

    def test_non_three_operation_count_rejected_even_bool(self):
        for value in (2, 4, True):
            raw = fixture()
            raw["input_operations"] = value
            self.assertIn("input_operations must", " ".join(audit(raw)["errors"]))

    def test_role_identity_tampering_rejected(self):
        raw = fixture()
        raw["apps"]["chromium"]["identity"]["matches"][0]["window"] = "123"
        self.assertIn("identity receipt", " ".join(audit(raw)["errors"]))

    def test_missing_transition_receipt_holds(self):
        raw = fixture()
        raw["ledger"] = [e for e in raw["ledger"] if e["kind"] != "focus_drift"]
        raw["event_count"] = len(raw["ledger"])
        result = audit(raw)
        self.assertTrue(result["errors"])
        self.assertTrue(any("focus drift" in h for h in result["holds"]))

    def test_unresolved_process_group_rejected(self):
        raw = fixture()
        raw["ledger"][-1]["processes"][0]["remaining_pids"] = [999]
        self.assertIn("cleanup receipt", " ".join(audit(raw)["errors"]))

    def test_bool_int_confusion_rejected(self):
        raw = fixture()
        raw["event_count"] = True
        self.assertIn("event_count/ledger length", " ".join(audit(raw)["errors"]))


if __name__ == "__main__":
    unittest.main()
