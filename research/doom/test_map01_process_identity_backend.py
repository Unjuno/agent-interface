from contextlib import contextmanager
from pathlib import Path
import sys
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


class SignalReader:
    def __init__(self, name): self.name = name
    def read_frame(self, observation, image):
        return {'format': 'observable-signal-v1', 'status': 'observed',
                'signal_id': self.name, 'value': 97 if self.name == 'health' else 20,
                'sequence': observation['sequence'], 'capture_ns': observation['capture_ns'],
                'binding': observation['pointer_binding'], 'wad_sha256': 'b' * 64}


@contextmanager
def backend_fixture():
    fake, events, generation = FakeDisplay(), [], ['a' * 64]
    fake.keysym_to_keycode = lambda value: {ord('a'): 38}.get(value, 0)
    class Reader:
        def read(self, operation, xid): return generation[0]
        def close(self): pass
    def emit(connection, event, code):
        if event == 2: fake.down.add(code)
        elif event == 3: fake.down.discard(code)
    binding = {'focus': 41, 'surface': 41, 'geometry': [0, 0, 32, 32]}
    with tempfile.TemporaryDirectory() as output, patch.object(
            native.display, 'Display', return_value=fake), patch.object(
            native.xtest, 'fake_input', side_effect=emit), patch.object(
            policy, 'X11TargetQueries', side_effect=lambda name: Reader()), patch.object(
            Previous, 'binding', return_value=binding), patch(
            'doom_typed_coast_backend_v1.ImageGrab.grab', return_value=Image.new('RGB', (32, 32), 'white')):
        session = SimpleNamespace(name=':fake', d=fake, context=lambda: {'windows': 'fixture'})
        backend = Backend(session, Path(output), events.append,
                          {name: SignalReader(name) for name in ('health', 'ammo')})
        try:
            yield backend, events, generation, fake
        finally:
            backend.close()


class ProcessBackendTests(unittest.TestCase):
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
