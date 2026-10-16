"""Actual selected MAP01 path with finite Fake X native-I/O stalls."""
from pathlib import Path
import json
import sys
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_map01_process_identity_backend import backend_fixture, Executor, native


class UnverifiedReleaseTests(unittest.TestCase):
    def test_stalled_native_io_retains_obligation_and_refuses_new_admission(self):
        for mode in ('press_send', 'release_send', 'release_sync', 'release_readback'):
            with self.subTest(mode=mode), backend_fixture() as (backend, events, generation, fake):
                backend.snapshot('source', 0)
                entered, resume, terminal_ready = threading.Event(), threading.Event(), threading.Event()
                release_sent = False
                presses = []
                original_emit = native.xtest.fake_input.side_effect
                original_sync, original_keymap = fake.sync, fake.query_keymap
                def stall():
                    entered.set()
                    if not resume.wait(5): raise RuntimeError('test native I/O not resumed')
                def send(connection, event, code):
                    nonlocal release_sent
                    if event == native.X.KeyPress:
                        presses.append(code)
                        if mode == 'press_send': stall()
                    if event == native.X.KeyRelease and mode == 'release_send': stall()
                    original_emit(connection, event, code)
                    if event == native.X.KeyRelease: release_sent = True
                def sync():
                    if mode == 'release_sync' and release_sent: stall()
                    return original_sync()
                def keymap():
                    if mode == 'release_readback' and release_sent: stall()
                    return original_keymap()
                def emit(row):
                    events.append(row)
                    if row.get('event') == 'terminal': terminal_ready.set()
                executor = Executor(backend, emit)
                try:
                    with patch.object(native.xtest, 'fake_input', side_effect=send), patch.object(
                            fake, 'sync', side_effect=sync), patch.object(fake, 'query_keymap', side_effect=keymap):
                        executor.submit('blocked', [{'op': 'hold', 'keys': ['a'], 'duration_ms': 5}],
                                        backend.sequence, time.perf_counter_ns() + 10_000_000_000)
                        worker = executor.active[2]
                        self.assertTrue(entered.wait(1))
                        with self.assertRaises(ValueError):
                            executor.submit('busy', [{'op': 'observe'}], backend.sequence,
                                            time.perf_counter_ns() + 1_000_000_000)
                        self.assertTrue(terminal_ready.wait(3))
                        worker.join(1)
                        terminal = next(row for row in events if row.get('event') == 'terminal')
                        self.assertEqual(terminal['status'], 'failed')
                        self.assertFalse(terminal['release']['verified'])
                        self.assertFalse(resume.is_set())
                        self.assertEqual(fake.down, {38} if mode == 'release_send' else set())
                        stalled_state = sorted(fake.down)
                        original_lease = backend.lease
                        backend.snapshot('fresh-after-failure', 0)
                        with patch.object(backend, 'validate', side_effect=AssertionError('validation reached')), patch.object(
                                backend, 'bind_lease_source', side_effect=AssertionError('binding reached')):
                            with self.assertRaisesRegex(ValueError, 'unverified'):
                                executor.submit('after-failure', [{'op': 'observe'}], backend.sequence,
                                                time.perf_counter_ns() + 1_000_000_000)
                        self.assertIs(backend.lease, original_lease)
                        self.assertNotIn('after-failure', executor.used_ids)
                        self.assertFalse(any(row.get('event') == 'accepted' and
                                             row.get('id') == 'after-failure' for row in events))
                        self.assertTrue(terminal['input_recovery_required'])
                        obligation = executor.release_obligation_snapshot()
                        self.assertEqual(obligation['id'], 'blocked')
                        self.assertEqual(obligation['intent_token'], backend.lease.intent_token)
                        self.assertEqual(obligation['valid_until_ns'], original_lease.deadline)
                        self.assertEqual(obligation['expected_sequence'], 1)
                        self.assertEqual(obligation['target_process_identity'], original_lease.target_process_identity)
                        obligation['release']['verified'] = True
                        self.assertFalse(executor.release_obligation_snapshot()['release']['verified'])
                        resume.set()
                        self.assertTrue(backend.owner._inner.stopped.wait(1))
                        self.assertEqual(fake.down, set())
                        self.assertEqual(presses, [38])
                        self.assertIsNotNone(executor.release_obligation_snapshot())
                        print(json.dumps({'mode': mode, 'stalled_fake_keys': stalled_state,
                            'terminal': terminal, 'new_admission_refused': True,
                            'final_fake_keys': sorted(fake.down), 'press_requests': presses,
                            'owner_stopped': backend.owner._inner.stopped.is_set(),
                            'obligation_after_late_return': executor.release_obligation_snapshot()}), flush=True)
                finally:
                    resume.set()
                    executor.close()

    def test_verified_cleanup_allows_next_fresh_program(self):
        with backend_fixture() as (backend, events, generation, fake):
            executor = Executor(backend, events.append)
            try:
                for identifier in ('first', 'second'):
                    backend.snapshot(identifier + '-source', 0)
                    executor.submit(identifier, [{'op': 'hold', 'keys': ['a'], 'duration_ms': 5}],
                                    backend.sequence, time.perf_counter_ns() + 1_000_000_000)
                    executor.active[2].join(1) if executor.active else None
                    terminal = next(row for row in events if row.get('event') == 'terminal' and row['id'] == identifier)
                    self.assertEqual(terminal['status'], 'completed')
                    self.assertTrue(terminal['release']['verified'])
                    self.assertIsNone(executor.release_obligation_snapshot())
                self.assertEqual(fake.down, set())
            finally:
                executor.close()


if __name__ == '__main__':
    unittest.main()
