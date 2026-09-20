import copy
import hashlib
import json
import unittest
from pathlib import Path

from audit_transition import audit

RAW_PATH = Path(__file__).parent / "evidence" / "formal-01" / "result.json"


def fixture():
    return json.loads(RAW_PATH.read_text(encoding="utf-8"))


def rehash(event):
    payload = {k: v for k, v in event.items() if k != "hash"}
    event["hash"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class ReconstructionTests(unittest.TestCase):
    def test_retained_raw_holds_only_for_missing_observation_receipts(self):
        result = audit(fixture())
        self.assertEqual(result["decision"], "HOLD_AUDIT_EVIDENCE_INCOMPLETE")
        self.assertEqual(result["error_count"], 0)
        self.assertIn("Chromium old-window-absence receipt is missing", result["holds"])
        self.assertIn("active-window observation at Calc return is missing", result["holds"])
        self.assertIn("raw does not provide three independently countable input-operation receipts", result["holds"])
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

    def test_semantic_focus_mutation_rejected_after_valid_rehash(self):
        raw = fixture()
        event = next(e for e in raw["ledger"] if e["kind"] == "focus_drift")
        event["active"] = "8389413"
        rehash(event)
        raw["checks"] = [True] * 5
        result = audit(raw)
        self.assertNotEqual(result["decision"], "PASS_AUDIT_RECONSTRUCTION_SCOPED")
        self.assertFalse(result["derived_transitions"]["focus_drift"])

    def test_semantic_modal_parent_mutation_rejected_after_valid_rehash(self):
        raw = fixture()
        event = next(e for e in raw["ledger"] if e["kind"] == "modal_transition")
        event["parent"] = "4194311"
        rehash(event)
        raw["checks"] = [True] * 5
        result = audit(raw)
        self.assertNotEqual(result["decision"], "PASS_AUDIT_RECONSTRUCTION_SCOPED")
        self.assertFalse(result["derived_transitions"]["modal"])

    def test_extra_event_with_valid_hash_rejected(self):
        raw = fixture()
        event = copy.deepcopy(raw["ledger"][1])
        event["seq"] = 1
        rehash(event)
        for index, existing in enumerate(raw["ledger"][1:], start=2):
            existing["seq"] = index
            rehash(existing)
        raw["ledger"].insert(1, event)
        raw["event_count"] = 16
        result = audit(raw)
        self.assertIn("exact 15-event protocol", " ".join(result["errors"]))

    def test_missing_and_incorrect_identity_receipts_hold(self):
        raw = fixture()
        replacement = next(e for e in raw["ledger"] if e["kind"] == "window_replacement")
        replacement["old_window_absent"] = {"observed": True}
        rehash(replacement)
        returned = next(e for e in raw["ledger"] if e["kind"] == "return_to_earlier_app")
        returned["active_window"] = "4194311"
        rehash(returned)
        result = audit(raw)
        self.assertNotEqual(result["decision"], "PASS_AUDIT_RECONSTRUCTION_SCOPED")
        self.assertIn("raw does not provide three independently countable input-operation receipts", result["holds"])

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
