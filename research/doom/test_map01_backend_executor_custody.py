"""Selected Fake X backend custody must outlive a failed Executor wrapper."""
from pathlib import Path
import json
import sys
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_map01_process_identity_backend import backend_fixture, Executor, native


class BackendCustodyTests(unittest.TestCase):
    def test_closed_unverified_executor_cannot_be_replaced_on_same_backend(self):
        with backend_fixture() as (backend, events, generation, fake):
            backend.snapshot('source', 0)
            entered, resume, terminal_ready = (threading.Event() for _ in range(3))
            def emit(row):
                events.append(row)
                if row.get('event') == 'terminal': terminal_ready.set()
            original_send = native.xtest.fake_input.side_effect
            def send(connection, event, code):
                if event == native.X.KeyRelease:
                    entered.set()
                    if not resume.wait(5): raise RuntimeError('test release gate was not resumed')
                return original_send(connection, event, code)
            first = Executor(backend, emit)
            replacement = None
            try:
                with patch.object(native.xtest, 'fake_input', side_effect=send):
                    first.submit('original', [{'op': 'hold', 'keys': ['a'], 'duration_ms': 5}],
                                 backend.sequence, time.perf_counter_ns() + 10_000_000_000)
                    self.assertTrue(entered.wait(1))
                    self.assertTrue(terminal_ready.wait(3))
                    first.close()
                    self.assertTrue(first.closed)
                    self.assertEqual(fake.down, {38})
                    obligation = first.release_obligation_snapshot()
                    self.assertIsNotNone(obligation)
                    original_lease = backend.lease
                    refused = False
                    try:
                        replacement = Executor(backend, events.append)
                        # No second positive input: characterize admission with
                        # an observation-only intent while original key is held.
                        replacement.submit('replacement', [{'op': 'observe'}], backend.sequence,
                                           time.perf_counter_ns() + 1_000_000_000)
                    except ValueError:
                        refused = True
                    snapshot = {'case': 'closed-executor-replacement-while-release-send-held',
                        'replacement_refused': refused,
                        'replacement_accepted': any(row.get('event') == 'accepted' and
                            row.get('id') == 'replacement' for row in events),
                        'original_closed': first.closed, 'original_obligation': obligation,
                        'backend_lease_changed': backend.lease is not original_lease,
                        'fake_keys_down': sorted(fake.down), 'native_resumed': resume.is_set()}
                    print(json.dumps(snapshot), flush=True)
                    self.assertTrue(refused, snapshot)
                    self.assertFalse(snapshot['replacement_accepted'])
                    self.assertFalse(snapshot['backend_lease_changed'])
                    self.assertFalse(resume.is_set())
                    custody = backend.executor_custody_snapshot()
                    self.assertTrue(custody['executor_attached'])
                    self.assertEqual(custody['release_obligation'], obligation)
                    custody['release_obligation']['release']['verified'] = True
                    self.assertFalse(backend.executor_custody_snapshot()['release_obligation']['release']['verified'])
                    resume.set()
                    self.assertTrue(backend.owner._inner.stopped.wait(1))
                    self.assertEqual(fake.down, set())
                    backend.snapshot('fresh-after-late-native-return', 0)
                    with self.assertRaisesRegex(ValueError, 'unverified'):
                        Executor(backend, events.append)
                    self.assertEqual(backend.executor_custody_snapshot()['release_obligation'], obligation)
                    print(json.dumps({'case': 'late-owner-return-does-not-reset-backend-custody',
                        'fake_keys_down': sorted(fake.down),
                        'custody': backend.executor_custody_snapshot()}), flush=True)
            finally:
                resume.set()
                if replacement is not None: replacement.close()
                first.close()

    def test_current_executor_occupies_backend_even_between_programs(self):
        with backend_fixture() as (backend, events, generation, fake):
            first = Executor(backend, events.append)
            try:
                with self.assertRaisesRegex(ValueError, 'occupied'):
                    Executor(backend, events.append)
                self.assertTrue(backend.executor_custody_snapshot()['executor_attached'])
                self.assertIsNone(backend.executor_custody_snapshot()['release_obligation'])
                self.assertFalse(any(row.get('event') == 'accepted' for row in events))
            finally: first.close()

    def test_verified_close_permits_healthy_replacement_and_is_idempotent(self):
        with backend_fixture() as (backend, events, generation, fake):
            for identifier in ('healthy-first', 'healthy-replacement'):
                executor = Executor(backend, events.append)
                try:
                    backend.snapshot(identifier + '-source', 0)
                    executor.submit(identifier, [{'op': 'hold', 'keys': ['a'], 'duration_ms': 5}],
                                    backend.sequence, time.perf_counter_ns() + 1_000_000_000)
                    executor.active[2].join(1) if executor.active else None
                    terminal = next(row for row in events if row.get('event') == 'terminal' and row['id'] == identifier)
                    self.assertTrue(terminal['release']['verified'])
                    self.assertEqual(fake.down, set())
                finally:
                    executor.close()
                    executor.close()
                custody = backend.executor_custody_snapshot()
                self.assertFalse(custody['executor_attached'])
                self.assertIsNone(custody['release_obligation'])

    def test_concurrent_constructors_cannot_claim_one_backend_twice(self):
        with backend_fixture() as (backend, events, generation, fake):
            gate = threading.Barrier(3)
            attached, refused = [], []
            def construct():
                gate.wait(timeout=2)
                try: attached.append(Executor(backend, events.append))
                except ValueError as error: refused.append(error)
            workers = [threading.Thread(target=construct) for _ in range(2)]
            for worker in workers: worker.start()
            try:
                gate.wait(timeout=2)
                for worker in workers: worker.join(1)
                self.assertTrue(all(not worker.is_alive() for worker in workers))
                self.assertEqual(len(attached), 1)
                self.assertEqual(len(refused), 1)
                self.assertTrue(backend.executor_custody_snapshot()['executor_attached'])
            finally:
                for executor in attached: executor.close()

    def test_wrong_token_cannot_clear_or_rewrite_backend_custody(self):
        with backend_fixture() as (backend, events, generation, fake):
            with self.assertRaises(ValueError): backend.claim_executor_custody(None)
            with self.assertRaises(ValueError): backend.release_executor_custody(None)
            with self.assertRaises(ValueError): backend.retain_executor_release_obligation(None, {'id': 'wrong'})
            first = Executor(backend, events.append)
            try:
                with self.assertRaisesRegex(ValueError, 'does not own'):
                    backend.release_executor_custody(object())
                with self.assertRaisesRegex(ValueError, 'does not own'):
                    backend.retain_executor_release_obligation(object(), {'id': 'wrong'})
                custody = backend.executor_custody_snapshot()
                self.assertTrue(custody['executor_attached'])
                self.assertIsNone(custody['release_obligation'])
            finally: first.close()


if __name__ == '__main__': unittest.main()
