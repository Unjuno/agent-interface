"""Regression and mutation tests for independent logical-key audit coverage."""
import copy
import json
import unittest
from pathlib import Path

from baseline_audit_v2 import audit as baseline_audit
from audit_v3 import audit as candidate_audit

ROOT = Path(__file__).parent

def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

class KeyIdentityAuditTests(unittest.TestCase):
    def setUp(self):
        self.expected = load("expected_inventory.json")
        self.raw = load("raw_input.json")["records"]

    def test_baseline_and_candidate_accept_pristine_raw(self):
        self.assertEqual(baseline_audit(self.expected, self.raw), [])
        self.assertEqual(candidate_audit(self.expected, self.raw), [])

    def test_baseline_accepts_corrupt_explicit_key_candidate_rejects(self):
        records = copy.deepcopy(self.raw)
        records[0]["key"] = "tampered-key"
        self.assertEqual(baseline_audit(self.expected, records), [])
        self.assertTrue(any(e.startswith("release_identity_mismatch:") for e in candidate_audit(self.expected, records)))

    def test_baseline_accepts_corrupt_cleanup_key_candidate_rejects(self):
        records = copy.deepcopy(self.raw)
        records[2]["key"] = "tampered-key"
        self.assertEqual(baseline_audit(self.expected, records), [])
        self.assertTrue(any(e.startswith("release_identity_mismatch:") for e in candidate_audit(self.expected, records)))

    def test_baseline_accepts_missing_explicit_key_candidate_rejects(self):
        records = copy.deepcopy(self.raw)
        del records[0]["key"]
        self.assertEqual(baseline_audit(self.expected, records), [])
        self.assertTrue(any(":missing:key" in e for e in candidate_audit(self.expected, records)))

    def test_baseline_accepts_missing_cleanup_key_candidate_rejects(self):
        records = copy.deepcopy(self.raw)
        del records[2]["key"]
        self.assertEqual(baseline_audit(self.expected, records), [])
        self.assertTrue(any(":missing:key" in e for e in candidate_audit(self.expected, records)))

    def test_candidate_accepts_null_cleanup_key(self):
        self.assertEqual(self.raw[2]["key"], None)
        self.assertEqual(candidate_audit(self.expected, self.raw), [])

    def test_candidate_rejects_non_string_non_null_key(self):
        records = copy.deepcopy(self.raw)
        records[2]["key"] = {"unexpected": "shape"}
        self.assertNotEqual(candidate_audit(self.expected, records), [])

if __name__ == "__main__":
    unittest.main(verbosity=2)
