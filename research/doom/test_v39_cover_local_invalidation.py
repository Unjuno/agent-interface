"""Local invalidation/release ordering; no provider, display or process launch."""
import json
import queue
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'live_control')]
import map01_overlap_controller_v39 as controller
from persistent_planner_adapter_v2 import PersistentPlannerAdapter, PlannerProtocolError


class Client:
    def __init__(self):
        self.interrupts = []
        self.closed = []
        self.turn = 0
    def start_thread(self, **params): return {'thread': {'id': 'thread'}}
    def start_turn(self, *args, **params):
        self.turn += 1
        return {'turn': {'id': f'turn-{self.turn}'}}
    def interrupt_turn(self, thread, turn):
        self.interrupts.append((thread, turn))
        return {}
    def close(self, timeout=5): self.closed.append(timeout)
    def wait_turn_completed(self, *args, **params):
        return {'turn': {'status': 'completed', 'items': [
            {'type': 'agentMessage', 'text': '{"action":"stale"}'}]}}
    def latest_turn_usage(self, *args): return None


def planner():
    client = Client()
    value = PersistentPlannerAdapter(client, model='mock', effort='low', cwd='.', base_instructions='')
    value.start_session()
    handle = value.begin_turn('observe', output_schema={'type': 'object'})
    return value, handle, client


class LocalInvalidationTests(unittest.TestCase):
    def test_selected_executor_stalled_release_is_saved_before_native_resume(self):
        from test_map01_process_identity_backend import backend_fixture, Executor, native
        with backend_fixture() as (backend, events, generation, fake), tempfile.TemporaryDirectory() as root:
            backend.snapshot('source', 0)
            incoming = queue.Queue()
            def emit(row):
                events.append(row)
                incoming.put(json.loads(json.dumps(row)))
            executor = Executor(backend, emit)
            value, handle, client = planner()
            entered, resume = threading.Event(), threading.Event()
            original_send = native.xtest.fake_input.side_effect
            def send(connection, event, code):
                if event == native.X.KeyRelease:
                    entered.set()
                    if not resume.wait(5): raise RuntimeError('test native release not resumed')
                return original_send(connection, event, code)
            def cancel(text):
                row = json.loads(text)
                self.assertEqual(row, {'op': 'cancel', 'id': 'stalled-cover'})
                self.assertTrue(value._cancellation_requested)
                executor.cancel(row['id'])
            def wait(predicate):
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    try: row = incoming.get(timeout=max(.001, deadline - time.monotonic()))
                    except queue.Empty: break
                    if predicate(row): return row
                raise TimeoutError('no Executor boundary')
            try:
                with patch.object(native.xtest, 'fake_input', side_effect=send):
                    executor.submit('stalled-cover', [{'op': 'hold', 'keys': ['a'], 'duration_ms': 5}],
                                    backend.sequence, time.perf_counter_ns() + 10_000_000_000)
                    self.assertTrue(entered.wait(1))
                    with self.assertRaisesRegex(RuntimeError, 'verify empty release') as caught:
                        controller.cancel_invalidated_cover(value, handle,
                            SimpleNamespace(stdin=SimpleNamespace(write=cancel, flush=lambda: None)),
                            wait, 'stalled-cover', failure_root=root)
                    receipt = json.loads((Path(root)/'cover-cancel-failure.json').read_text())
                    self.assertEqual(receipt, caught.exception.cover_cancellation_receipt)
                    self.assertEqual(fake.down, {38})
                    self.assertFalse(resume.is_set())
                    self.assertFalse(receipt['terminal']['release']['verified'])
                    self.assertEqual(receipt['terminal']['release_obligation'],
                                     json.loads(json.dumps(executor.release_obligation_snapshot())))
                    self.assertEqual(client.interrupts, [])
                    self.assertEqual(client.closed, [5])
                    print(json.dumps({'case': 'cover-release-stalled-before-native-resume',
                        'stalled_fake_keys': sorted(fake.down), 'native_resumed': resume.is_set(),
                        'remote_interrupts': client.interrupts, 'receipt': receipt}), flush=True)
            finally:
                resume.set()
                executor.close()

    def test_local_invalidation_does_not_consume_the_remote_request(self):
        value, handle, client = planner()
        receipt = value.invalidate_turn(handle)
        self.assertEqual(receipt['outcome'], 'locally_invalidated')
        self.assertEqual(client.interrupts, [])
        self.assertEqual(value.interrupt(handle)['outcome'], 'requested')
        self.assertEqual(value.interrupt(handle)['outcome'], 'already_requested')
        self.assertEqual(client.interrupts, [('thread', 'turn-1')])
        self.assertFalse(value.await_turn(handle).answer_eligible)

    def test_stale_invalidation_cannot_poison_a_fresh_turn(self):
        value, old, client = planner()
        value.await_turn(old)
        fresh = value.begin_turn('fresh', output_schema={'type': 'object'})
        with self.assertRaises(PlannerProtocolError): value.invalidate_turn(old)
        self.assertTrue(value.await_turn(fresh).answer_eligible)
        self.assertEqual(client.interrupts, [])

    def test_local_abort_cannot_be_followed_by_a_new_remote_interrupt(self):
        value, handle, client = planner()
        value.invalidate_turn(handle)
        self.assertEqual(value.abort_pending_turn()['outcome'], 'aborted')
        self.assertEqual(value.interrupt(handle)['outcome'], 'already_aborted')
        self.assertEqual(client.interrupts, [])

    def test_failed_release_saved_before_abort_without_remote_interrupt(self):
        value, handle, client = planner()
        terminal = {'event': 'terminal', 'id': 'cover', 'status': 'failed',
                    'release': {'event': 'owner_release', 'verified': False, 'keys_down': [38]}}
        writes = []
        process = SimpleNamespace(stdin=SimpleNamespace(write=writes.append, flush=lambda: None))
        def wait(predicate):
            self.assertTrue(value._cancellation_requested)
            self.assertEqual(len(writes), 1)
            self.assertEqual(client.interrupts, [])
            self.assertTrue(predicate(terminal))
            return terminal
        with tempfile.TemporaryDirectory() as root:
            def close(timeout=5):
                receipt = json.loads((Path(root)/'cover-cancel-failure.json').read_text())
                self.assertEqual(receipt['terminal'], terminal)
                self.assertFalse(receipt['grants_input_authority'])
                self.assertEqual(receipt['physical_input_state'], 'unverified')
                client.closed.append(timeout)
            client.close = close
            with self.assertRaisesRegex(RuntimeError, 'verify empty release'):
                controller.cancel_invalidated_cover(value, handle, process, wait, 'cover', failure_root=root)
        self.assertEqual(client.interrupts, [])
        self.assertEqual(client.closed, [5])

    def test_wait_failure_aborts_with_local_invalidation_retained(self):
        value, handle, client = planner()
        process = SimpleNamespace(stdin=SimpleNamespace(write=lambda row: None, flush=lambda: None))
        def wait(predicate): raise TimeoutError('no terminal')
        with self.assertRaisesRegex(TimeoutError, 'no terminal'):
            controller.cancel_invalidated_cover(value, handle, process, wait, 'cover')
        self.assertTrue(value._cancellation_requested)
        self.assertEqual(client.interrupts, [])
        self.assertEqual(client.closed, [5])

    def test_existing_failure_evidence_and_primary_error_survive_abort_error(self):
        value, handle, client = planner()
        process = SimpleNamespace(stdin=SimpleNamespace(write=lambda row: None, flush=lambda: None))
        terminal = {'event': 'terminal', 'id': 'cover', 'status': 'failed'}
        def close(timeout=5): raise OSError('synthetic close fault')
        client.close = close
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'cover-cancel-failure.json'
            path.write_text('original evidence\n')
            with self.assertRaisesRegex(RuntimeError, 'verify empty release') as caught:
                controller.cancel_invalidated_cover(value, handle, process, lambda predicate: terminal,
                                                    'cover', failure_root=root)
            self.assertEqual(path.read_text(), 'original evidence\n')
            self.assertIn('cover failure receipt save failed: FileExistsError', caught.exception.__notes__)
            self.assertIn('planner transport abort failed: OSError', caught.exception.__notes__)
            self.assertEqual(caught.exception.cover_cancellation_receipt['terminal'], terminal)


if __name__ == '__main__': unittest.main()
