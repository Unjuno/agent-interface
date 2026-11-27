import importlib.util
from pathlib import Path
import sys
import threading
import types
import unittest

HERE = Path(__file__).resolve().parent


class Parent:
    created_owners = []

    def __init__(self, session, out, emit, signal_readers):
        self.init_args = (session, out, emit, signal_readers)
        self.owner = Owner()
        self.created_owners.append(self.owner)

    def execute(self, step, cancel, identifier, index):
        if step.get('mode') == 'partial_raise':
            self.raw(step['keys'][0], False)
            raise RuntimeError('synthetic partial release')
        for key in step.get('keys', []):
            self.raw(key, False)
        return 'ok'

    def release_all(self):
        for key in list(self.held):
            self.raw(key, False)
        return {'verified': True, 'keys_down': [], 'buttons_down': []}

parent = types.ModuleType('doom_typed_release_backend_v1')
parent.Backend = Parent
parent.suite = object()
sys.modules['doom_typed_release_backend_v1'] = parent
wrapper = types.ModuleType('input_transition_owner_v3')
class FakeTransitionInputOwner:
    constructed = []

    def __init__(self, display_name):
        self.display_name = display_name
        self.inner = Owner()
        self.closed = False
        self.constructed.append(self)

    @property
    def owner_id(self):
        return self.inner.owner_id

    def call(self, *args, **kwargs):
        return self.inner.call(*args, **kwargs)

    def close(self):
        self.closed = True
        return self.inner.close()

wrapper.InputOwner = FakeTransitionInputOwner
sys.modules['input_transition_owner_v3'] = wrapper
spec = importlib.util.spec_from_file_location('doom_typed_release_backend_v3', HERE / 'doom_typed_release_backend_v3.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Lease:
    def __init__(self, token='intent-1'):
        self.intent_token = token


class Owner:
    def __init__(self, *, owned_after=None, owner_id='owner-1', sample_started=100,
                 ordinary=True, receipt_token='intent-1', cleanup_ns=None):
        self.calls = []
        self.owned_after = [] if owned_after is None else list(owned_after)
        self.owner_id = owner_id
        self.sample_started = sample_started
        self.ordinary = ordinary
        self.receipt_token = receipt_token
        self.records = []
        self.cleanup_ns = cleanup_ns
        self.explicit_key_release_requests = []
        self.release_index = 0
        self.closed = False

    def close(self):
        self.closed = True

    def call(self, op, lease=None, key=None):
        self.calls.append((op, key))
        if op == 'down':
            return {'event': 'input_admission', 'key': key, 'intent_token': getattr(lease, 'intent_token', None)}
        if op == 'up':
            self.release_index += 1
            returned = self.release_index * 10
            if self.cleanup_ns is not None:
                self.records.append({
                    'event': 'owner_release', 'verified': True,
                    'reason': 'cancelled', 'verified_ns': self.cleanup_ns,
                })
            else:
                self.explicit_key_release_requests.append(key)
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
    def test_backend_uses_current_release_base_and_transition_owner(self):
        candidate = (HERE / 'doom_typed_release_backend_v3.py').read_text(encoding='utf-8')
        self.assertIn(
            'from doom_typed_release_backend_v1 import Backend as Previous, suite',
            candidate)
        self.assertIn('from input_transition_owner_v3 import InputOwner', candidate)
        self.assertNotIn('from doom_typed_coast_backend_v1 import', candidate)

    def test_current_v39_session_selects_and_hashes_the_successor_backend(self):
        session = (HERE / 'session_map01_v12.py').read_text(encoding='utf-8')
        owner = (HERE.parent / 'live_control' / 'input_transition_owner_v3.py').read_text(
            encoding='utf-8')
        self.assertIn('from doom_typed_release_backend_v3 import Backend, suite', session)
        self.assertIn('HERE / "doom_typed_release_backend_v3.py"', session)
        self.assertIn('HERE.parent / "live_control/input_transition_owner_v3.py"', session)
        self.assertIn('from input_owner_v10 import InputOwner as Previous', owner)
        self.assertIn('(args.out / "x11-display.txt").write_text(session.name', session)

    def test_constructor_replaces_the_current_release_backend_owner(self):
        Parent.created_owners.clear()
        FakeTransitionInputOwner.constructed.clear()
        session = types.SimpleNamespace(name='display-7')
        emitted = []
        backend = mod.Backend(session, Path('/tmp/out'), emitted.append,
                              {'health': object(), 'ammo': object()})
        self.assertIs(backend.init_args[0], session)
        self.assertTrue(Parent.created_owners[-1].closed)
        selected = FakeTransitionInputOwner.constructed[-1]
        self.assertEqual(selected.display_name, 'display-7')
        self.assertIs(backend.owner, selected)
        self.assertFalse(selected.closed)

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

    def test_cleanup_inside_explicit_release_bracket_is_not_ordinary(self):
        owner = Owner(cleanup_ns=7)
        obj = make_backend({'a'}, owner, with_context=False)
        obj.execute({'keys': ['a']}, None, 'p', 0)
        row = obj.emitted[0]
        self.assertTrue(row['ordinary_release_candidate'] is False)
        self.assertTrue(row['owner_cleanup_records_available'])
        self.assertTrue(row['owner_cleanup_overlapped_release_call'])
        self.assertFalse(row['owner_transition_verified'])
        self.assertEqual(owner.explicit_key_release_requests, [])
        self.assertEqual([record['event'] for record in owner.records], ['owner_release'])

    def test_cleanup_outside_explicit_release_bracket_keeps_ordinary_release(self):
        obj = make_backend({'a'}, Owner(cleanup_ns=4))
        obj.raw('a', False)
        row = obj.emitted[0]
        self.assertTrue(row['ordinary_release_candidate'])
        self.assertTrue(row['owner_cleanup_records_available'])
        self.assertFalse(row['owner_cleanup_overlapped_release_call'])
        self.assertTrue(row['owner_transition_verified'])

    def test_missing_cleanup_log_fails_closed(self):
        owner = Owner()
        del owner.records
        obj = make_backend({'a'}, owner)
        obj.raw('a', False)
        self.assertFalse(obj.emitted[0]['owner_cleanup_records_available'])
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

    def test_two_key_release_batch_survives_successful_step_boundary(self):
        obj = make_backend({'a', 'space'}, with_context=False)
        obj.execute({'keys': ['a']}, None, 'p', 0)
        self.assertEqual(obj.emitted, [])
        self.assertEqual(obj.held, {'space'})

        obj.execute({'keys': ['space']}, None, 'p', 1)

        rows = [r for r in obj.emitted if r.get('event') == 'input_release_transition']
        self.assertEqual([row['key'] for row in rows], ['a', 'space'])
        self.assertEqual([row['release_batch_step'] for row in rows], [0, 1])
        self.assertEqual([row['release_batch_position'] for row in rows], [0, 1])
        samples = [op for op in obj.owner.calls if op[0] == 'input_state']
        self.assertEqual(samples, [('input_state', None)])

    def test_new_program_does_not_inherit_previous_program_receipts(self):
        obj = make_backend({'a', 'space'}, with_context=False)
        obj.execute({'keys': ['a']}, None, 'p', 0)
        obj.execute({'keys': ['space']}, None, 'q', 0)

        rows = [r for r in obj.emitted if r.get('event') == 'input_release_transition']
        self.assertEqual([row['key'] for row in rows], ['space'])
        self.assertEqual([row['release_batch_identifier'] for row in rows], ['q'])
        self.assertEqual([row['release_batch_step'] for row in rows], [0])

    def test_final_release_all_flushes_buffered_program_rows(self):
        obj = make_backend({'a', 'space'}, with_context=False)
        obj.execute({'keys': ['a']}, None, 'p', 0)
        self.assertEqual(obj.emitted, [])

        release = obj.release_all()

        rows = [r for r in obj.emitted if r.get('event') == 'input_release_transition']
        self.assertEqual(release['verified'], True)
        self.assertEqual([row['key'] for row in rows], ['a', 'space'])
        self.assertEqual([row['release_batch_step'] for row in rows], [0, 0])
        self.assertEqual(sum(op[0] == 'input_state' for op in obj.owner.calls), 1)

    def test_later_step_exception_discards_prior_buffered_rows(self):
        obj = make_backend({'a', 'space', 'd'}, with_context=False)
        obj.execute({'keys': ['a']}, None, 'p', 0)
        with self.assertRaisesRegex(RuntimeError, 'synthetic partial release'):
            obj.execute({'mode': 'partial_raise', 'keys': ['space']}, None, 'p', 1)

        self.assertFalse(hasattr(obj._release_batch, 'context'))
        self.assertEqual(obj.emitted, [])

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
