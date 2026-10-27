import unittest
from test_audit_a07_owner_release_reconciliation import fixture
from audit_a07_owner_release_reconciliation import audit
class KeymapErrorTest(unittest.TestCase):
 def test_error_cannot_be_accepted(self):
  for field in ('keymap_before_error','keymap_after_error'):
   with self.subTest(field=field):
    events,owner=fixture()
    events[6]['owner_release']['key_release_attempts']['40']['attempts'][0][field]='sample error'
    self.assertEqual(audit(events,owner)['status'],'FAIL')