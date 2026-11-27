import unittest
from test_audit_a07_owner_release_reconciliation import fixture
from audit_a07_owner_release_reconciliation import audit

class MissingAttemptErrorTest(unittest.TestCase):
    def test_each_missing_error_field_fails_closed(self):
        for field in ('keyrelease_error', 'sync_error', 'keymap_before_error', 'keymap_after_error'):
            with self.subTest(field=field):
                events, owner = fixture()
                attempt = events[6]['owner_release']['key_release_attempts']['40']['attempts'][0]
                del attempt[field]
                self.assertEqual(audit(events, owner)['status'], 'FAIL')