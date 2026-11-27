import unittest
from test_audit_a07_owner_release_reconciliation import fixture
from audit_a07_owner_release_reconciliation import audit

class AmbiguousAttempts(unittest.TestCase):
    def test_error_then_success_is_not_unambiguously_verified(self):
        events, owner = fixture()
        attempts=events[6]['owner_release']['key_release_attempts']['40']['attempts']
        bad=dict(attempts[0],keyrelease_error='backend error')
        attempts.insert(0,bad)
        self.assertEqual(audit(events,owner)['status'],'FAIL')