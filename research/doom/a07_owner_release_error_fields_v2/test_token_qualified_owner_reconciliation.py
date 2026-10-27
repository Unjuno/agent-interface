import copy
import unittest
from test_audit_a07_owner_release_reconciliation import fixture
from token_qualified_owner_reconciliation import audit

class TokenQualifiedTests(unittest.TestCase):
    def test_single_owner_receipt_cannot_serve_two_cancellations(self):
        events, owner = fixture()
        other = copy.deepcopy(events)
        for row in other: row["id"] = "cover-2"
        result = audit(events + other, owner)
        self.assertEqual(result["status"], "HOLD_AMBIGUOUS_TOKEN")
        self.assertFalse(result["formal_pass"])

    def test_missing_owner_error_is_not_promoted(self):
        events, owner = fixture()
        del events[6]["owner_release"]["key_release_attempts"]["40"]["attempts"][0]["sync_error"]
        self.assertEqual(audit(events, owner)["status"], "FAIL")

    def test_unique_token_retains_scoped_terminal_cleanup(self):
        events, owner = fixture()
        result = audit(events, owner)
        self.assertEqual(result["status"], "PASS_CUSTODY_RECONCILED_SCOPED")
        self.assertFalse(result["formal_pass"])

if __name__ == "__main__": unittest.main()
