"""Synthetic boundary for saved owner-release reconciliation; no live input."""
import copy
import unittest

from test_audit_a07_owner_release_reconciliation import fixture
from audit_a07_owner_release_reconciliation import audit


class OwnerReleaseTokenReuseBoundary(unittest.TestCase):
    def test_one_owner_event_is_counted_for_two_cancellations_with_same_token(self):
        events, owner_events = fixture()
        second = copy.deepcopy(events)
        for row in second:
            row["id"] = "cover-2"
        result = audit(events + second, owner_events)
        self.assertEqual(len(owner_events), 1)
        self.assertEqual(result["counts"]["cancellations"], 2)
        self.assertEqual(result["counts"]["passed_cancellations"], 2)
        self.assertEqual(result["status"], "PASS_CUSTODY_RECONCILED_SCOPED")
        self.assertFalse(result["formal_pass"])


if __name__ == "__main__":
    unittest.main()
