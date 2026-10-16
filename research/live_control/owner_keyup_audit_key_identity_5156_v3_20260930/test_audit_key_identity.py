import copy
import json
import unittest
from pathlib import Path

from audit_key_identity import audit_key_identity
from upstream.audit_v2 import audit as upstream_audit


ROOT = Path(__file__).resolve().parent
EXPECTED = json.loads((ROOT / "upstream/expected_inventory.json").read_text())
RECORDS = json.loads((ROOT / "upstream/retained_raw.json").read_text())["records"]


class KeyIdentityAuditTests(unittest.TestCase):
    def test_pristine_retained_raw_is_accepted_by_both_auditors(self):
        self.assertEqual(upstream_audit(EXPECTED, RECORDS), [])
        self.assertEqual(audit_key_identity(EXPECTED, RECORDS), [])

    def test_original_auditor_false_accepts_explicit_key_mutation(self):
        rows = copy.deepcopy(RECORDS)
        rows[0]["key"] = "b"
        self.assertEqual(upstream_audit(EXPECTED, rows), [])
        self.assertTrue(audit_key_identity(EXPECTED, rows))

    def test_original_auditor_false_accepts_cleanup_key_mutation(self):
        rows = copy.deepcopy(RECORDS)
        rows[2]["key"] = "b"
        self.assertEqual(upstream_audit(EXPECTED, rows), [])
        self.assertTrue(audit_key_identity(EXPECTED, rows))

    def test_explicit_key_must_be_exact_frozen_nonempty_string(self):
        for key in (None, False, 38, "", "other"):
            with self.subTest(key=key):
                rows = copy.deepcopy(RECORDS)
                rows[0]["key"] = key
                self.assertTrue(audit_key_identity(EXPECTED, rows))

    def test_autonomous_cleanup_key_must_remain_exact_null(self):
        for key in ("b", False, 0, 38, []):
            with self.subTest(key=key):
                rows = copy.deepcopy(RECORDS)
                rows[2]["key"] = key
                self.assertTrue(audit_key_identity(EXPECTED, rows))

    def test_missing_key_and_foreign_release_are_rejected(self):
        rows = copy.deepcopy(RECORDS)
        del rows[0]["key"]
        self.assertTrue(audit_key_identity(EXPECTED, rows))
        rows = copy.deepcopy(RECORDS)
        rows[0]["release_id"] = "foreign-release"
        self.assertTrue(audit_key_identity(EXPECTED, rows))

    def test_missing_and_duplicate_release_rows_are_rejected(self):
        self.assertTrue(audit_key_identity(EXPECTED, RECORDS[:2]))
        self.assertTrue(audit_key_identity(EXPECTED, [*RECORDS, RECORDS[0]]))

    def test_invalid_expected_key_contract_is_rejected(self):
        bad_explicit = [{**EXPECTED[0], "key": None}, *EXPECTED[1:]]
        bad_cleanup = [*EXPECTED[:2], {**EXPECTED[2], "key": "b"}]
        self.assertTrue(audit_key_identity(bad_explicit, RECORDS))
        self.assertTrue(audit_key_identity(bad_cleanup, RECORDS))


if __name__ == "__main__":
    unittest.main()
