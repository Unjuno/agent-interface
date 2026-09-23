import importlib.util
from pathlib import Path
import sys
import threading
import types
import unittest

HERE = Path(__file__).resolve().parent


class Parent:
    def execute(self, step, cancel, identifier, index):
        if step.get('mode') == 'partial_raise':
            self.raw(step['keys'][0], False)
            raise RuntimeError('synthetic partial release')
        for key in step.get('keys', []):
            self.raw(key, False)
        return 'ok'

parent = types.ModuleType('doom_typed_coast_backend_v1')
parent.Backend = Parent
parent.suite = object()
sys.modules['doom_typed_coast_backend_v1'] = parent
wrapper = types.ModuleType('input_transition_owner_v3')
wrapper.InputOwner = object
sys.modules['input_transition_owner_v3'] = wrapper
spec = importlib.util.spec_from_file_location('doom_retained_input_backend_v3', HERE / 'doom_retained_input_backend_v3.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Lease:
    def __init__(self, token='intent-1'):
        self.intent_token = token


class Owner:
    def __init__(self, *, owned_after=None, owner_id='owner-1', sample_started=100,
                 ordinary=True, receipt_token='intent-1'):
        self.calls = []
        self.owned_after = [] if owned_after is None else list(owned_after)
        self.owner_id = owner_id
        self.sample_started = sample_started
        self.ordinary = ordinary
        self.receipt_token = receipt_token
        self.release_index = 0

    def call(self, op, lease=None, key=None):
        self.calls.append((op, key))
        if op == 'down':
            return {'event': 'input_admission', 'key': key, 'intent_token': getattr(lease, 'intent_token', None)}
        if op == 'up':
            self.release_index += 1
            returned = self.release_index * 10
            return {
                'event': 'input_release_transition', 'operation': 'up', 'key': key,
                'owner_id': self.owner_id, 'intent_token': self.receipt_token,
                'release_call_started_ns': returned - 5,
                'release_call_returned_ns': returned,
                'ordinary_release_candidate': self.ordinary,
                'owner_transition_verified': None,
                'grants_input_authority': False,
            }
        if op == 'input_state':
            return {
                'owner_id': self.owner_id,
                'owned_keycodes': list(self.owned_after),
                'sample_started_ns': self.sample_started,
                'sample_finished_ns': self.sample_started + 10,
            }
        raise AssertionError(op)


def make_backend(held, owner=None, token='intent-1', with_context=True):
    obj = mod.Backend.__new__(mod.Backend)
    obj.owner = owner or Owner()
    obj.lease = Lease(token)
    obj.held = set(held)
    obj._release_batch = threading.local()
    if with_context:
        obj._release_batch.context = {'rows': [], 'identifier': 'p', 'step': 0}
    obj.emitted = []
    obj.emit = obj.emitted.append
    return obj


class Tests(unittest.TestCase):
    def test_two_key_order_has_one_sample_after_both_releases_then_emits(self):
        obj = make_backend({'a', 'space'})
        obj.raw('a', False)
        self.assertEqual(obj.owner.calls, [('up', 'a')])
        self.assertEqual(obj.emitted, [])
        obj.raw('space', False)
        self.assertEqual(obj.owner.calls, [('up', 'a'), ('up', 'space'), ('input_state', None)])
        self.assertEqual([row['key'] for row in obj.emitted], ['a', 'space'])
        self.assertTrue(all(row['owner_transition_verified'] for row in obj.emitted))
        self.assertEqual([row['release_batch_position'] for row in obj.emitted], [0, 1])

    def test_sample_order_failure_fails_closed(self):
        obj = make_backend({'a', 'd'}, Owner(sample_started=15))
        obj.raw('a', False); obj.raw('d', False)
        self.assertTrue(all(not row['owner_transition_verified'] for row in obj.emitted))
        self.assertTrue(all(not row['owner_sample_ordered_after_batch'] for row in obj.emitted))

    def test_owner_identity_mismatch_fails_closed(self):
        owner = Owner(owner_id='owner-1')
        obj = make_backend({'a'}, owner)
        original = owner.call
        def call(op, lease=None, key=None):
            row = original(op, lease, key)
            if op == 'input_state': row['owner_id'] = 'owner-2'
            return row
        owner.call = call
        obj.raw('a', False)
        self.assertFalse(obj.emitted[0]['owner_transition_verified'])
        self.assertFalse(obj.emitted[0]['owner_identity_matches_after_batch'])

    def test_nonempty_owner_state_fails_closed(self):
        obj = make_backend({'a'}, Owner(owned_after=[38]))
        obj.raw('a', False)
        self.assertFalse(obj.emitted[0]['owner_transition_verified'])
        self.assertEqual(obj.emitted[0]['owned_keycodes_after_batch'], [38])

    def test_backend_unowned_release_fails_closed(self):
        obj = make_backend(set())
        obj.raw('a', False)
        self.assertFalse(obj.emitted[0]['owner_transition_verified'])
        self.assertFalse(obj.emitted[0]['backend_owned_before_release'])

    def test_stale_ordinary_candidate_fails_closed(self):
        obj = make_backend({'a'}, Owner(ordinary=False))
        obj.raw('a', False)
        self.assertFalse(obj.emitted[0]['owner_transition_verified'])

    def test_intent_token_mismatch_fails_closed(self):
        obj = make_backend({'a'}, Owner(receipt_token='other'))
        obj.raw('a', False)
        self.assertFalse(obj.emitted[0]['owner_transition_verified'])
        self.assertFalse(obj.emitted[0]['intent_token_matches_after_batch'])

    def test_non_step_cleanup_releases_without_telemetry(self):
        obj = make_backend({'a'}, with_context=False)
        obj.raw('a', False)
        self.assertEqual(obj.owner.calls, [('up', 'a')])
        self.assertEqual(obj.emitted, [])
        self.assertEqual(obj.held, set())

    def test_execute_discards_partial_batch_after_exception(self):
        obj = make_backend({'a', 'd'}, with_context=False)
        with self.assertRaisesRegex(RuntimeError, 'partial release'):
            obj.execute({'mode': 'partial_raise', 'keys': ['a', 'd']}, object(), 'p', 0)
        self.assertFalse(hasattr(obj._release_batch, 'context'))
        self.assertEqual(obj.emitted, [])
        obj.raw('d', False)
        self.assertEqual(obj.emitted, [])

    def test_down_preserves_immediate_admission_emit(self):
        obj = make_backend(set())
        obj.raw('a', True)
        self.assertEqual(obj.owner.calls, [('down', 'a')])
        self.assertEqual(obj.held, {'a'})
        self.assertEqual(obj.emitted[0]['event'], 'input_admission')

    def test_existing_direct_analyzer_event_contract_is_preserved(self):
        obj = make_backend({'a'})
        obj.raw('a', False)
        row = obj.emitted[0]
        required = ('event', 'operation', 'key', 'intent_token',
                    'release_call_started_ns', 'release_call_returned_ns',
                    'owner_transition_verified')
        self.assertEqual(row['event'], 'input_release_transition')
        self.assertEqual(row['operation'], 'up')
        for key in required:
            self.assertIn(key, row)


if __name__ == '__main__':
    unittest.main(verbosity=2)
