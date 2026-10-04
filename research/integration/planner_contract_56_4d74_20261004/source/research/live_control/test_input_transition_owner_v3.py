import importlib.util
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent


class FakeInner:
    def __init__(self, display_name=':fake'):
        self.owner_id = 'owner-1'
        self.records = []
        self.calls = []
        self.result = None

    def call(self, operation, lease=None, key=None):
        self.calls.append((operation, key))
        return self.result

    def close(self):
        return None


base = types.ModuleType('input_owner_v10')
base.InputOwner = FakeInner
sys.modules['input_owner_v10'] = base
spec = importlib.util.spec_from_file_location('input_transition_owner_v3', HERE / 'input_transition_owner_v3.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Lease:
    def __init__(self, *, deadline=1000, cancelled=False, focus_invalid=False):
        self.intent_token = 'intent-1'
        self.deadline = deadline
        self.cancel = threading.Event()
        if cancelled:
            self.cancel.set()
        self.focus_invalid = focus_invalid


class Tests(unittest.TestCase):
    def test_ordinary_up_has_only_inner_up_and_valid_receipt(self):
        owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
        lease = Lease(deadline=1000)
        with mock.patch.object(mod.time, 'perf_counter_ns', side_effect=[100, 140]):
            row = owner.call('up', lease, 'a')
        self.assertEqual(owner._inner.calls, [('up', 'a')])
        self.assertEqual(row['event'], 'input_release_transition')
        self.assertEqual(row['transition_schema'], 'input-release-transition-v3')
        self.assertTrue(row['ordinary_release_candidate'])
        self.assertEqual(row['release_call_bracket_ns'], 40)
        self.assertEqual(row['intent_token'], 'intent-1')
        self.assertIs(row['grants_input_authority'], False)

    def test_cancelled_cleanup_is_not_ordinary(self):
        owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
        with mock.patch.object(mod.time, 'perf_counter_ns', side_effect=[100, 120]):
            row = owner.call('up', Lease(cancelled=True), 'a')
        self.assertFalse(row['ordinary_release_candidate'])
        self.assertTrue(row['cancel_requested_at_request'])

    def test_expired_cleanup_is_not_ordinary(self):
        owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
        with mock.patch.object(mod.time, 'perf_counter_ns', side_effect=[1000, 1020]):
            row = owner.call('up', Lease(deadline=1000), 'a')
        self.assertFalse(row['lease_time_valid_at_request'])
        self.assertFalse(row['ordinary_release_candidate'])

    def test_focus_invalid_cleanup_is_not_ordinary(self):
        owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
        with mock.patch.object(mod.time, 'perf_counter_ns', side_effect=[100, 120]):
            row = owner.call('up', Lease(focus_invalid=True), 'a')
        self.assertTrue(row['focus_invalid_at_request'])
        self.assertFalse(row['ordinary_release_candidate'])

    def test_button_up_has_no_state_query(self):
        owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
        with mock.patch.object(mod.time, 'perf_counter_ns', side_effect=[10, 20]):
            row = owner.call('button_up', Lease(), 1)
        self.assertEqual(owner._inner.calls, [('button_up', 1)])
        self.assertEqual(row['button'], 1)

    def test_non_release_delegates_and_decorates(self):
        owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
        owner._inner.result = {'event': 'input_admission'}
        row = owner.call('down', Lease(), 'a')
        self.assertEqual(owner._inner.calls, [('down', 'a')])
        self.assertEqual(row['intent_token'], 'intent-1')

    def test_changed_parent_release_contract_fails_closed(self):
        owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
        owner._inner.result = {'unexpected': True}
        with mock.patch.object(mod.time, 'perf_counter_ns', side_effect=[10, 20]):
            with self.assertRaisesRegex(AssertionError, 'unexpectedly returned payload'):
                owner.call('up', Lease(), 'a')

    def test_monotonic_regression_fails_closed(self):
        owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
        with mock.patch.object(mod.time, 'perf_counter_ns', side_effect=[20, 10]):
            with self.assertRaisesRegex(AssertionError, 'moved backwards'):
                owner.call('up', Lease(), 'a')


if __name__ == '__main__':
    unittest.main(verbosity=2)
