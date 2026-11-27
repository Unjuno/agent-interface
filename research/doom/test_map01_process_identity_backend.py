from contextlib import contextmanager
from pathlib import Path
import sys
import json
import threading
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'live_control'), str(HERE.parents[1])]
from test_input_owner_v12_explicit_up_cancel import FakeDisplay
import input_owner_v12 as native
import target_process_identity_v1 as policy
from executor_v13 import Executor
from executor_v3 import DecisionRequired
from doom_process_identity_backend_v1 import Backend
from doom_owner_thread_release_batch_backend_v1 import Backend as Previous
from input_owner_generation_protocol_v1 import InputOwnerGenerationProtocol
import map01_overlap_controller_v39 as controller


class SignalReader:
    def __init__(self, name): self.name = name
    def read_frame(self, observation, image):
        return {'format': 'observable-signal-v1', 'status': 'observed',
                'signal_id': self.name, 'value': 97 if self.name == 'health' else 20,
                'sequence': observation['sequence'], 'capture_ns': observation['capture_ns'],
                'binding': observation['pointer_binding'], 'wad_sha256': 'b' * 64}


@contextmanager
def backend_fixture(*, window_lifecycle=False, query_factory=None):
    fake, events, generation = FakeDisplay(), [], ['a' * 64]
    fake.keysym_to_keycode = lambda value: {ord('a'): 38}.get(value, 0)
    class Reader:
        def read(self, operation, xid):
            return fake.get_input_focus().focus if operation == 'focus_id' else generation[0]
        def close(self): pass
    def emit(connection, event, code):
        if event == 2: fake.down.add(code)
        elif event == 3: fake.down.discard(code)
    binding = {'focus': 41, 'surface': 41, 'geometry': [0, 0, 32, 32]}
    with tempfile.TemporaryDirectory() as output, patch.object(
            native.display, 'Display', return_value=fake), patch.object(
            native.xtest, 'fake_input', side_effect=emit), patch.object(
            policy, 'X11TargetQueries', side_effect=query_factory or (lambda name: Reader())), patch.object(
            Previous, 'binding', return_value=binding), patch(
            'doom_typed_coast_backend_v1.ImageGrab.grab', return_value=Image.new('RGB', (32, 32), 'white')):
        session = SimpleNamespace(name=':fake', d=fake, context=lambda: {'windows': 'fixture'})
        options = {'window_lifecycle': True} if window_lifecycle else {}
        backend = Backend(session, Path(output), events.append,
                          {name: SignalReader(name) for name in ('health', 'ammo')}, **options)
        try:
            yield backend, events, generation, fake
        finally:
            backend.close()


class ProcessBackendTests(unittest.TestCase):
    def test_cancelled_generation_rotates_owner_and_quarantines_late_reader(self):
        fake, events, generation, key_events = FakeDisplay(), [], ['a' * 64], []
        fake.keysym_to_keycode = lambda value: {ord('a'): 38, ord('b'): 56}.get(value, 0)
        entered, resume = threading.Event(), threading.Event()
        readers = []

        class Reader:
            def __init__(self, index): self.index = index; self.closed = threading.Event()
            def read(self, operation, xid):
                if operation == 'focus_id':
                    if self.index == 1 and fake.down:
                        entered.set()
                        if not resume.wait(3): raise RuntimeError('old query gate timed out')
                    return fake.get_input_focus().focus
                return generation[0]
            def close(self): self.closed.set()

        def factory(_display):
            reader = Reader(len(readers)); readers.append(reader); return reader

        def emit_key(connection, event, code):
            key_events.append((event, code))
            if event == 2: fake.down.add(code)
            elif event == 3: fake.down.discard(code)

        binding = {'focus': 41, 'surface': 41, 'geometry': [0, 0, 32, 32]}
        with tempfile.TemporaryDirectory() as output, patch.object(
                native.display, 'Display', return_value=fake), patch.object(
                native.xtest, 'fake_input', side_effect=emit_key), patch.object(
                policy, 'X11TargetQueries', side_effect=factory), patch.object(
                Previous, 'binding', return_value=binding), patch(
                'doom_typed_coast_backend_v1.ImageGrab.grab',
                return_value=Image.new('RGB', (32, 32), 'white')):
            session = SimpleNamespace(name=':fake', d=fake,
                                      context=lambda: {'windows': 'fixture'})
            backend = Backend(session, Path(output), events.append,
                              {name: SignalReader(name) for name in ('health', 'ammo')})
            first = None
            second = None
            try:
                backend.snapshot('source-0', 0)
                first = Executor(backend, events.append)
                first.submit('old-action', [{'op': 'hold', 'keys': ['a'],
                                             'duration_ms': 500}],
                             backend.sequence, time.perf_counter_ns() + 2_000_000_000)
                self.assertTrue(entered.wait(1))
                backend.lease.set()
                first.active[2].join(1)
                terminal = next(row for row in events if row.get('event') == 'terminal'
                                and row.get('id') == 'old-action')
                protocol = InputOwnerGenerationProtocol()
                protocol.record_terminal(terminal, backend)
                self.assertEqual(terminal['status'], 'cancelled')
                self.assertTrue(terminal['release']['verified'])
                self.assertEqual(fake.down, set())
                self.assertTrue(terminal['release']['target_process_identity_reader']['pending'])
                holder = {'executor': first}
                test_case = self
                real_snapshot = backend.snapshot
                capture_failures = [1]
                def flaky_snapshot(identifier, index):
                    if capture_failures:
                        capture_failures.pop()
                        raise DecisionRequired('synthetic transient passive capture refusal')
                    return real_snapshot(identifier, index)
                backend.snapshot = flaky_snapshot

                class Stdin:
                    def write(self, payload):
                        command = json.loads(payload)
                        if command['op'] == 'rotate_input_owner':
                            replacement, receipt = protocol.rotate(
                                command, executor=holder['executor'], backend=backend,
                                executor_factory=lambda selected: Executor(selected, events.append))
                            holder['executor'] = replacement
                            events.append(receipt)
                            with test_case.assertRaises(DecisionRequired):
                                backend.bind_lease_source(SimpleNamespace(
                                    deadline=time.perf_counter_ns() + 1_000_000_000),
                                    backend.sequence)
                        else:
                            try:
                                refreshed = protocol.refresh_source(command, backend=backend)
                            except Exception as error:
                                events.append({'event': 'rejected', 'id': command['id'],
                                               'terminal_id': command['id'],
                                               'operation': 'refresh_owner_source',
                                               'attempt': protocol._refresh_attempts,
                                               'reason': str(error)})
                            else:
                                events.append(refreshed)
                    def flush(self): pass

                generation[0] = 'b' * 64
                previous_sequence = backend.sequence
                def wait(predicate, timeout=40):
                    return next(row for row in reversed(events) if predicate(row))
                rotation = controller.rotate_retired_owner_after_cancel(
                    SimpleNamespace(stdin=Stdin()), wait, terminal,
                    minimum_sequence=previous_sequence)
                self.assertEqual(rotation['generation'], 1)
                self.assertEqual(rotation['source_refresh']['attempt'], 2)
                self.assertEqual(rotation['source_observation']['id'],
                                 'owner-generation-source-1-2')
                self.assertEqual(rotation['quarantined_readers'], 1)
                self.assertEqual(rotation['previous_owner_id'], terminal['input_owner_id'])
                fresh = rotation['source_observation']
                self.assertGreater(fresh['sequence'], previous_sequence)
                self.assertEqual(fresh['input_owner_generation'], 1)
                self.assertEqual(fresh['target_process_identity']['digest'], 'b' * 64)
                next_owner_id = backend.owner.owner_id
                with self.assertRaisesRegex(ValueError, 'already consumed'):
                    backend.rotate_input_owner_after_cancel(terminal)
                with self.assertRaisesRegex(ValueError, 'terminal'):
                    backend.rotate_input_owner_after_cancel(dict(terminal, status='completed'))

                def fresh_planner_turn(source):
                    if source['sequence'] <= previous_sequence:
                        raise AssertionError('planner requires the post-rotation source')
                    return {'turn_id': 'fresh-turn-1', 'source_sequence': source['sequence'],
                            'steps': [{'op': 'hold', 'keys': ['b'], 'duration_ms': 5}]}
                decision = fresh_planner_turn(fresh)
                self.assertEqual(decision['source_sequence'], fresh['sequence'])
                second = holder['executor']
                second.submit('new-action', decision['steps'],
                              backend.sequence, time.perf_counter_ns() + 1_000_000_000)
                second.active[2].join(1)
                new_terminal = next(row for row in events if row.get('event') == 'terminal'
                                    and row.get('id') == 'new-action')
                self.assertEqual(new_terminal['status'], 'completed')
                self.assertEqual(new_terminal['release']['target_process_identity'][2], 'b' * 64)
                self.assertEqual(key_events.count((2, 38)), 1)
                self.assertEqual(key_events.count((3, 38)), 1)
                self.assertEqual(key_events.count((2, 56)), 1)
                self.assertEqual(key_events.count((3, 56)), 1)
                blocked_rotation = {'event': 'terminal', 'id': 'blocked-third-generation',
                    'status': 'cancelled', 'input_owner_generation': 1,
                    'input_owner_id': next_owner_id,
                    'release': {'verified': True, 'keys_down': [],
                    'buttons_down': [], 'keys_unknown': [], 'key_state_errors': [],
                    'target_process_identity_reader': {'retired': True}}}
                protocol.record_terminal(blocked_rotation, backend)
                with self.assertRaisesRegex(RuntimeError, 'failed closed'):
                    protocol.rotate({'op': 'rotate_input_owner',
                                     'id': blocked_rotation['id']},
                        executor=second, backend=backend,
                        executor_factory=lambda _backend: self.fail('quarantine cap must refuse'))
                self.assertTrue(second.closed)
                self.assertEqual(backend.owner.owner_id, next_owner_id)
                self.assertEqual(backend._owner_generation, 1)
                source_before_late = backend._source_identity
                resume.set()
                self.assertTrue(readers[1].closed.wait(1))
                self.assertEqual(backend._source_identity, source_before_late)
                self.assertEqual(fake.down, set())
                self.assertEqual(backend.executor_custody_snapshot()['release_obligation'], None)
            finally:
                resume.set()
                if second is not None: second.close()
                if first is not None: first.close()
                backend.close()

    def test_actual_executor_cancel_releases_while_selected_focus_reader_stalls(self):
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('source', 0)
            entered, resume = threading.Event(), threading.Event()
            def focus():
                if fake.down:
                    entered.set()
                    if not resume.wait(3): raise RuntimeError('test focus not resumed')
                return SimpleNamespace(focus=41)
            fake.get_input_focus = focus
            executor = Executor(backend, events.append)
            try:
                executor.submit('blocked-focus', [{'op': 'hold', 'keys': ['a'], 'duration_ms': 500}],
                                backend.sequence, time.perf_counter_ns() + 2_000_000_000)
                self.assertTrue(entered.wait(1))
                backend.lease.set()
                executor.active[2].join(1) if executor.active else None
                terminals = [row for row in events if row.get('event') == 'terminal']
                self.assertTrue(terminals)
                self.assertNotEqual(terminals[-1]['status'], 'completed')
                self.assertTrue(terminals[-1]['release']['verified'])
                self.assertEqual(fake.down, set())
                self.assertFalse(resume.is_set())
                self.assertTrue(backend.owner._inner.identity_reader.worker.snapshot()['retired'])
            finally:
                resume.set()
                executor.close()

    def test_actual_capture_and_executor_admission_reach_selected_owner(self):
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('source', 0)
            source = [row for row in events if row.get('event') == 'observation'][-1]
            self.assertEqual(source['target_process_identity']['digest'], 'a' * 64)
            self.assertEqual(set(source['pointer_binding']), {'focus', 'surface', 'geometry'})
            executor = Executor(backend, events.append)
            try:
                executor.submit('program', [{'op': 'hold', 'keys': ['a'], 'duration_ms': 5}],
                                backend.sequence, time.perf_counter_ns() + 1_000_000_000)
                executor.active[2].join(2) if executor.active else None
                terminals = [v for v in events if v.get('event') == 'terminal' and v.get('id') == 'program']
                self.assertEqual(terminals[-1]['status'], 'completed')
                self.assertTrue(terminals[-1]['release']['verified'])
                self.assertEqual(fake.down, set())
            finally:
                executor.close()

    def test_changed_identity_refuses_before_new_keypress(self):
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('source', 0)
            generation[0] = 'b' * 64
            executor = Executor(backend, events.append)
            try:
                executor.submit('stale', [{'op': 'hold', 'keys': ['a'], 'duration_ms': 5}],
                                backend.sequence, time.perf_counter_ns() + 1_000_000_000)
                executor.active[2].join(2) if executor.active else None
                terminals = [v for v in events if v.get('event') == 'terminal' and v.get('id') == 'stale']
                self.assertNotEqual(terminals[-1]['status'], 'completed')
                admissions = [v for v in backend.owner.records if v.get('event') == 'input_admission']
                self.assertEqual(admissions, [])
                self.assertEqual(fake.down, set())
            finally:
                executor.close()

    def test_capture_generation_change_publishes_no_source(self):
        with backend_fixture() as (backend, events, generation, fake):
            with patch('doom_typed_coast_backend_v1.ImageGrab.grab',
                       side_effect=lambda **kwargs: (generation.__setitem__(0, 'b' * 64) or Image.new('RGB', (32, 32)))):
                with self.assertRaises(DecisionRequired): backend.snapshot('changed', 0)
            self.assertFalse(any(v.get('event') in ('observation', 'typed_observation') for v in events))
            with self.assertRaises(DecisionRequired):
                backend.bind_lease_source(SimpleNamespace(deadline=time.perf_counter_ns() + 1_000_000), backend.sequence)

    def test_accepted_callback_cannot_rebind_existing_lease_to_new_observation(self):
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('old-source', 0)
            def emit(row):
                events.append(row)
                if row.get('event') == 'accepted':
                    generation[0] = 'b' * 64
                    backend.snapshot('new-source', 0)
                    with self.assertRaises(DecisionRequired):
                        backend.bind_lease_source(backend.lease, backend.sequence)
            executor = Executor(backend, emit)
            try:
                executor.submit('pinned', [{'op': 'hold', 'keys': ['a'], 'duration_ms': 5}],
                                backend.sequence, time.perf_counter_ns() + 1_000_000_000)
                executor.active[2].join(2) if executor.active else None
                self.assertEqual(backend.lease.target_process_identity[2], 'a' * 64)
                self.assertEqual(backend._source_identity[2], 'b' * 64)
                self.assertFalse(any(v.get('event') == 'input_admission' for v in backend.owner.records))
            finally:
                executor.close()

    def test_missing_capture_refuses_before_accepted_publication(self):
        with backend_fixture() as (backend, events, generation, fake):
            executor = Executor(backend, events.append)
            try:
                with self.assertRaises(DecisionRequired):
                    executor.submit('missing', [{'op': 'observe'}], 0, time.perf_counter_ns() + 1_000_000_000)
                self.assertFalse(any(v.get('event') == 'accepted' for v in events))
            finally:
                executor.close()
