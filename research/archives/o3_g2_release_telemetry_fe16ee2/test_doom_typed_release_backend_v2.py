"""Offline deterministic regression for v11/v2 release-edge telemetry."""
from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BaseOwner:
    def call(self, operation, lease=None, key=None):
        return None


# Load v11 against a controlled v10 parent; the wrapper itself is under test.
base_owner_module = types.ModuleType('input_owner_v10')
base_owner_module.InputOwner = BaseOwner
sys.modules['input_owner_v10'] = base_owner_module
owner11 = load('input_owner_v11', HERE / 'input_owner_v11.py')


class ParentBackend:
    def __init__(self, *args, **kwargs):
        raise AssertionError('constructor not used by offline raw() regression')


parent_backend_module = types.ModuleType('doom_typed_release_backend_v1')
parent_backend_module.Backend = ParentBackend
parent_backend_module.suite = object()
sys.modules['doom_typed_release_backend_v1'] = parent_backend_module

# v2 imports Xlib.XK. The pure string mapping does not open a display.
backend2 = load('doom_typed_release_backend_v2', HERE / 'doom_typed_release_backend_v2.py')


class Lease:
    def __init__(self, cause=None):
        self.deadline = 9_999_999_999
        self.cause = cause

    def interruption_snapshot(self):
        return self.cause


class FakeDisplay:
    def __init__(self, code=38, down=False, fail=False):
        self.code = code
        self.down = down
        self.fail = fail

    def keysym_to_keycode(self, keysym):
        if self.fail:
            raise RuntimeError('query path unavailable')
        return self.code

    def query_keymap(self):
        bitmap = bytearray(32)
        if self.down:
            bitmap[self.code // 8] |= 1 << (self.code % 8)
        return bytes(bitmap)


class FakeOwner:
    def __init__(self, records):
        self.records = list(records)
        self.calls = []

    def call(self, operation, lease=None, key=None):
        self.calls.append((operation, key))
        return self.records.pop(0)


def owner_without_thread(cause=None):
    obj = object.__new__(owner11.InputOwner)
    obj.owner_id = 'owner-test'
    lease = Lease(cause)
    return obj, lease


def test_owner_ordinary():
    obj, lease = owner_without_thread()
    with mock.patch.object(BaseOwner, 'call', return_value=None), \
         mock.patch.object(owner11.time, 'perf_counter_ns', side_effect=[100, 140]):
        row = obj.call('up', lease, 'a')
    assert row['event'] == 'input_release_ack'
    assert row['release_requested_ns'] == 100
    assert row['release_ack_ns'] == 140
    assert row['release_attribution'] == 'ordinary_up'
    assert row['owner_id'] == 'owner-test'
    assert row['grants_input_authority'] is False


def test_owner_preexisting_release():
    cause = {'record': {'event': 'owner_release', 'reason': 'focus_changed',
                        'verified_ns': 77}}
    obj, lease = owner_without_thread(cause)
    with mock.patch.object(BaseOwner, 'call', return_value=None), \
         mock.patch.object(owner11.time, 'perf_counter_ns', side_effect=[100, 140]):
        row = obj.call('up', lease, 'a')
    assert row['release_attribution'] == 'superseded_before_request'
    assert row['interruption_reason'] == 'focus_changed'
    assert row['interruption_verified_ns'] == 77


def test_owner_raced_release():
    obj, lease = owner_without_thread()

    def raced(self, operation, lease_arg=None, key=None):
        lease.cause = {'record': {'event': 'owner_release', 'reason': 'expired',
                                  'verified_ns': 125}}
        return None

    with mock.patch.object(BaseOwner, 'call', raced), \
         mock.patch.object(owner11.time, 'perf_counter_ns', side_effect=[100, 140]):
        row = obj.call('up', lease, 'a')
    assert row['release_attribution'] == 'raced_owner_release'
    assert row['interruption_reason'] == 'expired'


def test_owner_non_up_delegates_unchanged():
    obj, lease = owner_without_thread()
    sentinel = {'event': 'input_admission', 'input_ack_ns': 88}
    with mock.patch.object(BaseOwner, 'call', return_value=sentinel) as parent, \
         mock.patch.object(owner11.time, 'perf_counter_ns') as clock:
        row = obj.call('down', lease, 'a')
    assert row is sentinel
    parent.assert_called_once_with('down', lease, 'a')
    clock.assert_not_called()


def test_owner_rejects_changed_v10_up_contract():
    obj, lease = owner_without_thread()
    with mock.patch.object(BaseOwner, 'call', return_value={'unexpected': True}), \
         mock.patch.object(owner11.time, 'perf_counter_ns', side_effect=[100, 140]):
        try:
            obj.call('up', lease, 'a')
        except AssertionError as exc:
            assert 'v10 up contract changed' in str(exc)
        else:
            raise AssertionError('changed parent up contract must fail closed')


def backend(records, *, down=False, fail=False, held=None):
    obj = object.__new__(backend2.Backend)
    obj.owner = FakeOwner(records)
    obj.lease = Lease()
    obj.held = set(held or {'a'})
    obj.session = types.SimpleNamespace(d=FakeDisplay(down=down, fail=fail))
    emitted = []
    obj.emit = emitted.append
    return obj, emitted


def release_record(key='a', attribution='ordinary_up'):
    return {
        'event': 'input_release_ack', 'key': key,
        'release_requested_ns': 10, 'release_ack_ns': 20,
        'release_attribution': attribution, 'grants_input_authority': False,
    }


def test_backend_verified_up():
    obj, emitted = backend([release_record()], held={'a', 'd'})
    with mock.patch.object(backend2.time, 'perf_counter_ns', return_value=30):
        obj.raw('a', False)
    assert obj.held == {'d'}
    row = emitted[0]
    assert row['physical_verified_up'] is True
    assert row['physical_key_down'] is False
    assert row['physical_verified_ns'] == 30
    assert row['physical_verification_authoritative'] is False


def test_backend_external_down_is_observed_not_failed():
    obj, emitted = backend([release_record()], down=True)
    with mock.patch.object(backend2.time, 'perf_counter_ns', return_value=31):
        obj.raw('a', False)
    assert emitted[0]['physical_verified_up'] is False
    assert emitted[0]['physical_key_down'] is True


def test_backend_verification_failure_is_fail_closed_telemetry():
    obj, emitted = backend([release_record()], fail=True)
    with mock.patch.object(backend2.time, 'perf_counter_ns', return_value=32):
        obj.raw('a', False)
    row = emitted[0]
    assert row['physical_verified_up'] is None
    assert row['physical_key_down'] is None
    assert 'query path unavailable' in row['physical_verification_error']
    assert obj.held == set()


def test_multi_key_release_emits_per_key_rows():
    obj, emitted = backend([release_record('a'), release_record('d')], held={'a', 'd'})
    with mock.patch.object(backend2.time, 'perf_counter_ns', side_effect=[40, 50]):
        obj.raw('a', False)
        obj.raw('d', False)
    assert obj.held == set()
    assert [row['key'] for row in emitted] == ['a', 'd']
    assert all(row['physical_verified_up'] is True for row in emitted)


def test_superseded_cleanup_is_labeled_not_reinterpreted():
    obj, emitted = backend([release_record('a', 'superseded_before_request')], held={'a'})
    with mock.patch.object(backend2.time, 'perf_counter_ns', return_value=60):
        obj.raw('a', False)
    assert emitted[0]['release_attribution'] == 'superseded_before_request'
    assert emitted[0]['physical_verified_up'] is True


def test_source_surface_is_telemetry_only():
    owner_source = (HERE / 'input_owner_v11.py').read_text()
    backend_source = (HERE / 'doom_typed_release_backend_v2.py').read_text()
    assert 'def _run(' not in owner_source
    assert "if operation != 'up':" in owner_source
    assert 'recovery' not in owner_source.lower()
    assert 'def raw(' in backend_source
    assert 'def validate(' not in backend_source
    assert 'def execute(' not in backend_source


def main():
    tests = [value for name, value in sorted(globals().items()) if name.startswith('test_') and callable(value)]
    for test in tests:
        test()
    print(f'PASS release-edge telemetry offline regression {len(tests)}/{len(tests)}')


if __name__ == '__main__':
    main()
