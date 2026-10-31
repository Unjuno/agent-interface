"""Exploratory contract for explicitly serialized, idle read-only capture."""
from types import SimpleNamespace
import threading
import time
import unittest
import tempfile
from unittest.mock import patch

from runtime.backends.x11_v1.backend import X11BackendError
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.guarded_x11_v1.target_queries import TargetQueryWorker
from runtime.cli_v1.test_mcp_process_identity import FakeX
from runtime.guarded_x11_v1.test_observation_worker import reader_backend


class BoundedIdleObservationContract(unittest.TestCase):
    def test_dedicated_capture_scope_refuses_later_keyboard_input(self):
        fake = FakeX(self)
        fake.backend.d.get_display_name = lambda: ':fake-idle'
        fake.backend.d.create_resource_object = lambda kind, xid: SimpleNamespace(id=xid)
        image = lambda *args: SimpleNamespace(data=fake.raw, depth=24, visual=1)
        backend = reader_backend(fake, image)
        backend.d.create_resource_object = lambda kind, xid: SimpleNamespace(id=xid)
        with tempfile.TemporaryDirectory() as td, \
             patch('runtime.guarded_x11_v1.observation_worker.open_readonly_backend', return_value=backend), \
             patch('runtime.guarded_x11_v1.observation_worker.read_linux_x11_process_identity', return_value=fake.generation), \
             patch('runtime.guarded_x11_v1.target_queries.X11TargetQueries') as query:
            query.return_value.read.side_effect = lambda op,xid: True if op=='focus' else fake.generation
            bridge = NativeHandleBridge(':fake-idle', {'app':20}, 'app', td+'/bridge',
                                        process_identity=True, query_worker=True, observation_worker=True)
            try:
                with bridge.cancellation_scope('idle-only', cancel_when_idle=True, single_idle_observation=True):
                    observation = bridge.observe_idle_until(time.monotonic_ns() + 2_000_000_000)
                    offset = bridge.mint('field', observation['sequence'], [8,8], region_size=[12,12])
                    with self.assertRaisesRegex(RuntimeError, 'single idle observation'):
                        bridge.keyboard('field', offset, tail=[{'op':'key_chord','keys':['CTRL','a']}])
                    activation = bridge.activate_window(window_id=20, source_sequence=observation['sequence'],
                        current_binding_revision=bridge.binding_revision,
                        expires_at_ns=time.monotonic_ns()+1_000_000_000, timeout_ms=10)
                    self.assertEqual(activation['error'], 'SINGLE_IDLE_OBSERVATION_SCOPE')
                    self.assertFalse(activation['input_dispatched'])
                    self.assertEqual(fake.emissions, [])
            finally:
                bridge.close()

    def test_real_reader_publishes_verified_fake_x_capture(self):
        fake = FakeX(self)
        fake.backend.d.get_display_name = lambda: ':fake-idle'
        image = lambda *args: SimpleNamespace(data=fake.raw, depth=24, visual=1)
        backend = reader_backend(fake, image)
        backend.d.create_resource_object = lambda kind, xid: SimpleNamespace(id=xid)
        with tempfile.TemporaryDirectory() as td, \
             patch('runtime.guarded_x11_v1.observation_worker.open_readonly_backend', return_value=backend), \
             patch('runtime.guarded_x11_v1.observation_worker.read_linux_x11_process_identity', return_value=fake.generation):
            bridge = NativeHandleBridge(':fake-idle', {'app':20}, 'app', td+'/bridge',
                                        process_identity=True, query_worker=True, observation_worker=True)
            try:
                with bridge.cancellation_scope('idle-capture', cancel_when_idle=True, single_idle_observation=True):
                    observation = bridge.observe_idle_until(time.monotonic_ns() + 2_000_000_000)
                    self.assertEqual(observation['sequence'], 1)
                    self.assertEqual(observation['pointer_binding']['process_generation'], fake.generation)
                    self.assertEqual(bridge.history[1][1].size, (32, 32))
                    self.assertEqual(bridge.request_cancel('idle-capture')['status'], 'not_active')
                    self.assertEqual(fake.emissions, [])
            finally:
                bridge.close()

    def make_bridge(self, reader):
        bridge = object.__new__(NativeHandleBridge)
        bridge.scope = 'test'; bridge.binding_revision = 1
        bridge.backend = SimpleNamespace(targets={'app': SimpleNamespace(id=20)})
        bridge.target = 'app'; bridge.sequence = 0; bridge.history = {}
        bridge.active = None; bridge.deadline = None; bridge._closed = False
        bridge.review_required = False; bridge._window_lifecycle_guard = False
        bridge._cancel_lock = threading.Lock(); bridge._cancel_ticket = None
        bridge._observations = TargetQueryWorker(lambda: reader)
        return bridge

    def test_healthy_capture_publishes_one_new_source(self):
        image = object()
        class Reader:
            def read(self, operation, request):
                return ({'sequence': request['payload']['sequence']}, image)
            def close(self): pass
        bridge = self.make_bridge(Reader())
        try:
            result = bridge.observe_idle_until(time.monotonic_ns() + 1_000_000_000)
            self.assertEqual(result['sequence'], 1)
            self.assertEqual(bridge.sequence, 1)
            self.assertIs(bridge.history[1][1], image)
        finally:
            bridge._observations.close()

    def test_cancel_after_committed_observation_is_not_acknowledged(self):
        class Reader:
            def read(self, operation, request): return ({'sequence': 1}, object())
            def close(self): pass
        bridge = self.make_bridge(Reader())
        bridge._target_queries = object(); bridge._used_cancel_tokens = set()
        try:
            with bridge.cancellation_scope('completed-idle', cancel_when_idle=True, single_idle_observation=True):
                result = bridge.observe_idle_until(time.monotonic_ns() + 1_000_000_000)
                self.assertEqual(result['sequence'], 1)
                self.assertEqual(bridge.request_cancel('completed-idle')['status'], 'not_active')
                self.assertFalse(bridge.review_required)
        finally:
            bridge._observations.close()

    def test_completed_idle_capture_does_not_disable_later_active_cancel(self):
        class Reader:
            def read(self, operation, request): return ({'sequence': 1}, object())
            def close(self): pass
        bridge = self.make_bridge(Reader())
        bridge._target_queries = object(); bridge._used_cancel_tokens = set()
        try:
            with bridge.cancellation_scope('multi-stage', cancel_when_idle=True):
                with self.assertRaises(X11BackendError):
                    bridge.observe_idle_until(time.monotonic_ns() + 1_000_000_000)
                bridge.active = ('later-action',)
                self.assertEqual(bridge.request_cancel('multi-stage')['status'], 'cancel_requested')
        finally:
            bridge._observations.close()

    def test_dedicated_scope_cannot_be_reused_for_second_capture(self):
        class Reader:
            def read(self, operation, request): return ({'sequence': request['payload']['sequence']}, object())
            def close(self): pass
        bridge = self.make_bridge(Reader())
        bridge._target_queries = object(); bridge._used_cancel_tokens = set()
        try:
            with bridge.cancellation_scope('one-capture', cancel_when_idle=True, single_idle_observation=True):
                bridge.observe_idle_until(time.monotonic_ns() + 1_000_000_000)
                with self.assertRaises(X11BackendError):
                    bridge.observe_idle_until(time.monotonic_ns() + 1_000_000_000)
                self.assertEqual(bridge.sequence, 1)
        finally:
            bridge._observations.close()

    def test_changed_binding_discards_result_and_retires_reader(self):
        entered, resume = threading.Event(), threading.Event()
        class Reader:
            def read(self, operation, request):
                entered.set()
                if not resume.wait(2): raise RuntimeError('fixture timed out')
                return ({'sequence': 1}, object())
            def close(self): pass
        bridge = self.make_bridge(Reader()); errors = []
        def call():
            try: bridge.observe_idle_until(time.monotonic_ns() + 1_000_000_000)
            except Exception as error: errors.append(error)
        worker = threading.Thread(target=call)
        try:
            worker.start(); self.assertTrue(entered.wait(1))
            bridge.binding_revision = 2; resume.set(); worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(len(errors), 1)
            self.assertIsInstance(errors[0], X11BackendError)
            self.assertEqual(bridge.sequence, 0); self.assertEqual(bridge.history, {})
            self.assertTrue(bridge.review_required)
            self.assertTrue(bridge._observations.snapshot()['retired'])
        finally:
            resume.set(); worker.join(2); bridge._observations.close()

    def test_binding_change_during_publication_never_publishes_stale_source(self):
        entered, resume = threading.Event(), threading.Event()
        class BlockingHistory(dict):
            def __setitem__(self, key, value):
                entered.set()
                if not resume.wait(2): raise RuntimeError('fixture timed out')
                super().__setitem__(key, value)
        class Reader:
            def read(self, operation, request): return ({'sequence': 1}, object())
            def close(self): pass
        bridge = self.make_bridge(Reader()); bridge.history = BlockingHistory(); errors = []
        def call():
            try: bridge.observe_idle_until(time.monotonic_ns() + 1_000_000_000)
            except Exception as error: errors.append(error)
        worker = threading.Thread(target=call)
        try:
            worker.start(); self.assertTrue(entered.wait(1))
            bridge.binding_revision = 2; resume.set(); worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(len(errors), 1)
            self.assertIsInstance(errors[0], X11BackendError)
            self.assertEqual(bridge.sequence, 0); self.assertEqual(bridge.history, {})
        finally:
            resume.set(); worker.join(2); bridge._observations.close()

    def test_public_cancel_during_publication_does_not_return_a_source(self):
        entered, resume = threading.Event(), threading.Event()
        class BlockingHistory(dict):
            def __setitem__(self, key, value):
                entered.set()
                if not resume.wait(2): raise RuntimeError('fixture timed out')
                super().__setitem__(key, value)
        class Reader:
            def read(self, operation, request): return ({'sequence': 1}, object())
            def close(self): pass
        bridge = self.make_bridge(Reader()); bridge.history = BlockingHistory()
        bridge._target_queries = object(); bridge._used_cancel_tokens = set()
        results, errors = [], []
        def call():
            try: results.append(bridge.observe_idle_until(time.monotonic_ns() + 1_000_000_000))
            except Exception as error: errors.append(error)
        worker = threading.Thread(target=call)
        with bridge.cancellation_scope('idle-observation', cancel_when_idle=True, single_idle_observation=True):
            try:
                worker.start(); self.assertTrue(entered.wait(1))
                cancellation = bridge.request_cancel('idle-observation')
                self.assertEqual(cancellation['status'], 'cancel_requested')
                resume.set(); worker.join(2)
                self.assertFalse(worker.is_alive())
                self.assertEqual(results, [])
                self.assertEqual(len(errors), 1)
                self.assertIsInstance(errors[0], X11BackendError)
                self.assertEqual(bridge.sequence, 0); self.assertEqual(bridge.history, {})
            finally:
                resume.set(); worker.join(2); bridge._observations.close()

    def test_commit_wins_before_later_cancel_is_acknowledged(self):
        entered, resume = threading.Event(), threading.Event()
        class PausedBridge(NativeHandleBridge):
            def __setattr__(self, name, value):
                if name == 'sequence' and value == 1:
                    entered.set()
                    if not resume.wait(2): raise RuntimeError('fixture timed out')
                super().__setattr__(name, value)
        class Reader:
            def read(self, operation, request): return ({'sequence': 1}, object())
            def close(self): pass
        original = self.make_bridge(Reader())
        bridge = object.__new__(PausedBridge); bridge.__dict__.update(original.__dict__)
        bridge._target_queries = object(); bridge._used_cancel_tokens = set()
        results, errors, cancellations = [], [], []
        def call():
            try: results.append(bridge.observe_idle_until(time.monotonic_ns() + 1_000_000_000))
            except Exception as error: errors.append(error)
        worker = threading.Thread(target=call)
        canceller = threading.Thread(target=lambda: cancellations.append(bridge.request_cancel('idle-publication')))
        with bridge.cancellation_scope('idle-publication', cancel_when_idle=True, single_idle_observation=True):
            try:
                worker.start(); self.assertTrue(entered.wait(1))
                canceller.start(); resume.set(); worker.join(2); canceller.join(2)
                self.assertFalse(worker.is_alive()); self.assertFalse(canceller.is_alive())
                self.assertEqual(errors, []); self.assertEqual(results[0]['sequence'], 1)
                self.assertEqual(cancellations[0]['status'], 'not_active')
                self.assertEqual(bridge.sequence, 1)
            finally:
                resume.set(); worker.join(2); canceller.join(2); bridge._observations.close()

    def test_blocked_capture_expires_without_publishing_late_frame(self):
        # A buggy implementation that publishes after timeout must fail even
        # if the reader eventually produces a seemingly valid frame.
        bridge = object.__new__(NativeHandleBridge)
        bridge.scope = 'test'; bridge.binding_revision = 1
        bridge.backend = SimpleNamespace(targets={'app': SimpleNamespace(id=20)})
        bridge.target = 'app'; bridge.sequence = 0; bridge.history = {}
        bridge.active = None; bridge.deadline = None; bridge._closed = False
        bridge.review_required = False; bridge._window_lifecycle_guard = False
        bridge._cancel_lock = threading.Lock(); bridge._cancel_ticket = None
        entered, resume, closed = (threading.Event() for _ in range(3))

        class Reader:
            def read(self, operation, request):
                entered.set()
                if not resume.wait(2): raise RuntimeError('fixture timed out')
                return ({'sequence': 1}, object())
            def close(self): closed.set()

        bridge._observations = TargetQueryWorker(Reader)
        self.assertTrue(hasattr(bridge, 'observe_idle_until'),
                        'bounded idle observation entry point is absent')
        try:
            started = time.monotonic_ns()
            with self.assertRaises(X11BackendError):
                bridge.observe_idle_until(started + 100_000_000)
            self.assertTrue(entered.is_set())
            self.assertTrue(bridge.review_required)
            self.assertEqual(bridge.sequence, 0)
            self.assertEqual(bridge.history, {})
            self.assertTrue(bridge._observations.snapshot()['retired'])
            resume.set()
            self.assertTrue(closed.wait(2))
            self.assertEqual(bridge.sequence, 0)
            self.assertEqual(bridge.history, {})
        finally:
            resume.set()
            bridge._observations.close()
