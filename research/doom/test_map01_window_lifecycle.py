"""Actual capture -> lease -> V4/V12/Executor with real lifecycle reader, Fake X."""
from contextlib import contextmanager
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import patch
from PIL import Image
sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]/'live_control'), str(Path(__file__).resolve().parents[2])]
from test_map01_process_identity_backend import backend_fixture
from executor_v13 import Executor
from executor_v3 import DecisionRequired
from runtime.guarded_x11_v1.target_queries import X11TargetQueries
from runtime.guarded_x11_v1.test_window_lifecycle import LifecycleConnection
from Xlib import X


@contextmanager
def fixture():
    connections = []
    def factory(name):
        connection = LifecycleConnection()
        connection.get_input_focus = lambda: type('Focus', (), {'focus':41})()
        connections.append(connection)
        reader = object.__new__(X11TargetQueries)
        reader.connection, reader._windows, reader._lifecycle_retired = connection, {}, False
        return reader
    with patch('runtime.guarded_x11_v1.target_queries.read_linux_x11_process_identity', return_value='a'*64):
        with backend_fixture(window_lifecycle=True, query_factory=factory) as row:
            yield (*row, connections)


class WindowLifecycleTests(unittest.TestCase):
    def monitor(self, connections):
        watches = [c for c in connections if c.selections]
        self.assertEqual(len(watches), 1)
        return watches[0]

    def finish(self, executor, identifier, events):
        if executor.active: executor.active[2].join(2)
        terminals = [r for r in events if r.get('event')=='terminal' and r.get('id')==identifier]
        self.assertTrue(terminals)
        return terminals[-1]

    def test_one_canonical_reader_transports_capture_lease_and_admission(self):
        with fixture() as (backend, events, generation, fake, connections):
            backend.snapshot('source', 0)
            source = [r for r in events if r.get('event')=='observation'][-1]
            self.assertEqual(self.monitor(connections).selections, [(41, X.StructureNotifyMask)])
            self.assertIs(backend.owner._inner.window_reader, backend.window_identity)
            executor = Executor(backend, events.append)
            try:
                executor.submit('healthy', [{'op':'hold','keys':['a'],'duration_ms':5}], backend.sequence, time.perf_counter_ns()+1_000_000_000)
                result = self.finish(executor, 'healthy', events)
                self.assertEqual(result['status'], 'completed')
                self.assertTrue(result['release']['verified'])
                self.assertEqual(backend.lease.target_window_identity[2], source['target_window_identity']['digest'])
                admissions = [r for r in events if r.get('event')=='input_admission']
                self.assertTrue(admissions)
                self.assertEqual(admissions[-1]['target_window_identity'], list(backend.lease.target_window_identity))
                self.assertEqual(fake.down, set())
            finally: executor.close()

    def test_same_process_destroy_reuse_refuses_old_observation(self):
        with fixture() as (backend, events, generation, fake, connections):
            backend.snapshot('source', 0)
            self.monitor(connections).event(X.DestroyNotify, xid=41)
            executor = Executor(backend, events.append)
            try:
                executor.submit('stale', [{'op':'hold','keys':['a'],'duration_ms':5}], backend.sequence, time.perf_counter_ns()+1_000_000_000)
                result = self.finish(executor, 'stale', events)
                self.assertNotEqual(result['status'], 'completed')
                self.assertFalse(any(r.get('event')=='input_admission' for r in events))
                self.assertEqual(fake.down, set())
            finally: executor.close()

    def test_destroy_during_capture_cannot_publish_or_bind_source(self):
        with fixture() as (backend, events, generation, fake, connections):
            def capture(**kwargs):
                self.monitor(connections).event(X.DestroyNotify, xid=41)
                return Image.new('RGB', (32,32), 'white')
            with patch('doom_typed_coast_backend_v1.ImageGrab.grab', side_effect=capture):
                with self.assertRaises(DecisionRequired): backend.snapshot('changed', 0)
            self.assertFalse(any(r.get('event') in ('observation','typed_observation') for r in events))

    def test_final_focus_query_cannot_replace_pinned_window_source(self):
        with fixture() as (backend, events, generation, fake, connections):
            backend.snapshot('source', 0)
            original = backend.owner._inner.identity_reader.read_focus
            calls = 0
            def focus(*args, **kwargs):
                nonlocal calls
                calls += 1
                value = original(*args, **kwargs)
                if calls == 2:
                    source = backend.lease.target_window_identity
                    backend.lease.target_window_identity = (*source[:2], 'b'*64, source[3])
                return value
            backend.owner._inner.identity_reader.read_focus = focus
            executor = Executor(backend, events.append)
            try:
                executor.submit('changed-source', [{'op':'hold','keys':['a'],'duration_ms':5}], backend.sequence, time.perf_counter_ns()+1_000_000_000)
                self.assertNotEqual(self.finish(executor,'changed-source',events)['status'],'completed')
                self.assertFalse(any(r.get('event')=='input_admission' for r in events))
                self.assertEqual(fake.down,set())
            finally: executor.close()

    def blocked(self, trigger, overlap=False):
        with fixture() as (backend, events, generation, fake, connections):
            backend.snapshot('source', 0)
            monitor = self.monitor(connections)
            entered, resume = threading.Event(), threading.Event()
            def attributes():
                if fake.down:
                    entered.set()
                    if not resume.wait(4): raise TimeoutError('test did not resume')
            monitor.on_attributes = attributes
            executor = Executor(backend, events.append)
            try:
                deadline = time.perf_counter_ns() + (200_000_000 if trigger=='expiry' else 2_000_000_000)
                executor.submit('blocked', [{'op':'hold','keys':['a'],'duration_ms':1500}], backend.sequence, deadline)
                self.assertTrue(entered.wait(1))
                self.assertEqual(fake.down, {38})
                if overlap:
                    with self.assertRaises(DecisionRequired): backend.snapshot('overlap', 0)
                if trigger=='cancel': backend.lease.set()
                result = self.finish(executor, 'blocked', events)
                self.assertNotEqual(result['status'], 'completed')
                self.assertTrue(result['release']['verified'])
                self.assertEqual(fake.down, set())
                self.assertFalse(resume.is_set())
                self.assertTrue(backend.window_identity.worker.snapshot()['retired'])
            finally:
                resume.set(); executor.close()

    def test_cancel_blocked_shared_lifecycle_releases_before_resume(self): self.blocked('cancel')
    def test_expiry_blocked_shared_lifecycle_releases_before_resume(self): self.blocked('expiry')
    def test_capture_query_overlap_refuses_without_second_monitor_or_release_wait(self): self.blocked('cancel', overlap=True)


if __name__=='__main__': unittest.main()
