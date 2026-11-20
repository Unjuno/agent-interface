"""Focused corruption controls for the independent retained-source auditor."""
import copy
import json
import lzma
import unittest
from pathlib import Path

from . import audit


class SavedSourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads(lzma.decompress(audit.SOURCE.read_bytes()))

    def test_exact_retained_summary(self):
        result = audit.audit_document(self.document)
        self.assertEqual(result["sample_total"], 194)
        self.assertEqual(result["physical_down_up_joins"], 3)
        self.assertEqual(result["attack_positive_endpoint_transitions"], 0)
        self.assertEqual(result["noinput_positive_endpoint_transitions"], 0)

    def test_missing_session_is_rejected(self):
        changed = copy.deepcopy(self.document)
        del changed["p3-noinput"]
        with self.assertRaisesRegex(audit.AuditError, "session inventory"):
            audit.audit_document(changed)

    def test_release_adapter_identity_mismatch_is_rejected(self):
        changed = copy.deepcopy(self.document)
        rows = [json.loads(row) for row in changed["p1-attack"]["events_exact_jsonl"]]
        release = next(row for row in rows if row.get("event") == "input_release_transition")
        release["physical_key_measurement"]["adapter_edge"]["actuation_id"] = "forged"
        changed["p1-attack"]["events_exact_jsonl"] = [json.dumps(row) for row in rows]
        with self.assertRaisesRegex(audit.AuditError, "measurement actuation mismatch"):
            audit.audit_document(changed)

    def test_positive_scorer_endpoint_is_rejected(self):
        changed = copy.deepcopy(self.document)
        rows = [json.loads(row) for row in changed["p1-attack"]["scorer_samples_exact_jsonl"]]
        rows[-1]["payload"]["map_exit"] = True
        changed["p1-attack"]["scorer_samples_exact_jsonl"] = [json.dumps(row) for row in rows]
        with self.assertRaisesRegex(audit.AuditError, "positive endpoint state"):
            audit.audit_document(changed)


if __name__ == "__main__":
    unittest.main()
