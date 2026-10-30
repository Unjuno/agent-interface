"""Synthetic timing boundary for historical owner-release reconciliation."""
import copy
import unittest

from audit_a07_owner_release_reconciliation import audit
from test_audit_a07_owner_release_reconciliation import fixture


class OwnerReleaseTimingBoundary(unittest.TestCase):
    def test_missing_timestamps_are_accepted_by_historical_auditor(self):
        events, owner_events = fixture()
        for row in events:
            if row.get('event') == 'input_admission':
                row.pop('admitted_ns', None)
            if row.get('event') == 'cancel_requested':
                row.pop('requested_ns', None)
        result = audit(events, owner_events)
        self.assertEqual(result['status'], 'PASS_CUSTODY_RECONCILED_SCOPED')
        self.assertFalse(result['formal_pass'])
        self.assertTrue(result['cancellations'][0]['checks']['no_post_cancel_admission'])

    def test_equal_timestamps_are_accepted_by_historical_auditor(self):
        events, owner_events = fixture()
        for row in events:
            if row.get('event') == 'input_admission':
                row['admitted_ns'] = 30
        result = audit(events, owner_events)
        self.assertEqual(result['status'], 'PASS_CUSTODY_RECONCILED_SCOPED')
        self.assertFalse(result['formal_pass'])


if __name__ == '__main__':
    unittest.main()
