"""Deterministic unit checks for non-perturbing release receipts."""
import importlib.util
import pathlib
import sys
import types
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent


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
spec = importlib.util.spec_from_file_location('input_transition_owner_v2', HERE / 'input_transition_owner_v2.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


class Lease:
    intent_token = 'intent-1'
    deadline = 999


def test_up_has_no_post_state_call():
    owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
    with mock.patch.object(mod.time, 'perf_counter_ns', side_effect=[10, 20]):
        row = owner.call('up', Lease(), 'a')
    assert owner._inner.calls == [('up', 'a')]
    assert row['event'] == 'input_release_receipt_v2'
    assert row['release_call_started_ns'] == 10 and row['release_call_returned_ns'] == 20
    assert row['intent_token'] == 'intent-1'


def test_button_up_has_no_post_state_call():
    owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
    with mock.patch.object(mod.time, 'perf_counter_ns', side_effect=[30, 40]):
        row = owner.call('button_up', Lease(), 1)
    assert owner._inner.calls == [('button_up', 1)]
    assert row['button'] == 1


def test_down_delegates_and_decorates_token():
    owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
    owner._inner.result = {'event': 'input_admission'}
    row = owner.call('down', Lease(), 'a')
    assert owner._inner.calls == [('down', 'a')]
    assert row['intent_token'] == 'intent-1'


def test_parent_release_contract_change_fails_closed():
    owner = mod.InputOwner(':fake', _owner_cls=FakeInner)
    owner._inner.result = {'unexpected': True}
    with mock.patch.object(mod.time, 'perf_counter_ns', side_effect=[1, 2]):
        try:
            owner.call('up', Lease(), 'a')
        except AssertionError:
            pass
        else:
            raise AssertionError('changed v10 explicit-release contract must fail')


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    for test in tests: test()
    print(f'PASS input transition owner v2 {len(tests)}/{len(tests)}')


if __name__ == '__main__': main()
