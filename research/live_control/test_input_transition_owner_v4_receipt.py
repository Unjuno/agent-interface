import importlib.util
from pathlib import Path
import sys
import threading
import time
import unittest

import test_input_owner_keyup_receipt as owner_fixture

HERE = Path(__file__).resolve().parent


class OwnerThreadTransitionReceiptTests(owner_fixture.OwnerKeyUpReceiptTests):
    def setUp(self):
        super().setUp()
        owner_v10_spec = importlib.util.spec_from_file_location(
            'input_owner_v10', HERE / 'input_owner_v10.py')
        owner_v10 = importlib.util.module_from_spec(owner_v10_spec)
        sys.modules['input_owner_v10'] = owner_v10
        owner_v10_spec.loader.exec_module(owner_v10)
        transition_spec = importlib.util.spec_from_file_location(
            'input_transition_owner_v4', HERE / 'input_transition_owner_v4.py')
        self.transition_module = importlib.util.module_from_spec(transition_spec)
        sys.modules['input_transition_owner_v4'] = self.transition_module
        transition_spec.loader.exec_module(self.transition_module)

    def tearDown(self):
        sys.modules.pop('input_transition_owner_v4', None)
        sys.modules.pop('input_owner_v10', None)
        super().tearDown()

    def test_cleanup_before_queued_up_has_no_owner_explicit_keyup_receipt(self):
        owner = self.transition_module.InputOwner(
            ':fake', _owner_cls=self.owner_module.InputOwner)
        try:
            lease = owner_fixture.Lease()
            owner.call('down', lease, 'a')
            lease.cancel.set()
            deadline = time.monotonic() + 1
            while not any(record.get('event') == 'owner_release'
                          and record.get('reason') == 'cancelled'
                          for record in owner.records):
                if time.monotonic() >= deadline:
                    self.fail('owner cancellation cleanup did not complete')
                threading.Event().wait(0.001)

            row = owner.call('up', lease, 'a')
            self.assertIsNone(row.get('owner_thread_keyup_receipt'))
            self.assertIs(row.get('owner_thread_keyup_verified'), False)
            self.assertFalse(row['ordinary_release_candidate'])
            self.assertEqual(self.displays[0].events, [(2, 38), (3, 38)])
        finally:
            owner.close()
    def test_transition_receipt_contains_nested_owner_thread_release_bracket(self):
        owner = self.transition_module.InputOwner(
            ':fake', _owner_cls=self.owner_module.InputOwner)
        try:
            lease = owner_fixture.Lease()
            self.assertEqual(owner.call('down', lease, 'a')['event'], 'input_admission')
            row = owner.call('up', lease, 'a')
            receipt = row.get('owner_thread_keyup_receipt')
            self.assertIsInstance(receipt, dict)
            self.assertTrue(row['owner_thread_keyup_verified'])
            self.assertTrue(row['ordinary_release_candidate'])
            self.assertLessEqual(row['release_call_started_ns'],
                                 receipt['owner_keyrelease_started_ns'])
            self.assertLessEqual(receipt['owner_keyrelease_started_ns'],
                                 receipt['owner_sync_returned_ns'])
            self.assertLessEqual(receipt['owner_sync_returned_ns'],
                                 row['release_call_returned_ns'])
        finally:
            owner.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)



