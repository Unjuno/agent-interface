"""Finite V39 caller boundary checks; no provider/display/process launch."""
import copy
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
from test_running_action_guard_v3 import guard_v3
from test_running_action_guard_v2 import COMMANDS, admission, program, snapshot, action, compiler
from running_action_guard_v3 import RunningActionGuardV3
from action_validity_admission_v1 import CONTRACT_FORMAT, action_fingerprint


def armed():
    guard = guard_v3()
    value = program('primary', COMMANDS[:1], [0])
    submit, accepted = admission('p1', value)
    accepted['intent_token'] = 'lease-token-1'
    guard.admit_program(value, submit, accepted)
    guard.check_current(snapshot(3, 300, health=20), 301)
    return guard


def rows():
    return [
        {'event': 'cancel_requested', 'id': 'p1', 'matched': True, 'requested_ns': 302},
        {'event': 'input_released', 'id': 'p1', 'intent_token': 'lease-token-1',
         'owner_release': {'event': 'owner_release', 'reason': 'cancelled', 'verified': True,
                           'keys_down': [], 'buttons_down': [], 'verified_ns': 303,
                           'valid_until_ns': 1000},
         'published_ns': 304, 'program_terminal_pending': True, 'grants_input_authority': False},
        {'event': 'terminal', 'id': 'p1', 'status': 'cancelled', 'terminal_ns': 310,
         'release': {'verified': True, 'keys_down': [], 'buttons_down': [], 'verified_ns': 309}},
    ]


class Stream:
    def __init__(self): self.writes = []
    def write(self, value): self.writes.append(value)
    def flush(self): pass


def waiter(values):
    pending = iter(copy.deepcopy(values))
    def wait(predicate):
        for row in pending:
            if predicate(row): return row
        raise TimeoutError('no matching boundary; supplied terminal was discarded')
    return wait


class CancelFailureTests(unittest.TestCase):
    def test_actual_selected_executor_failed_terminal_is_saved_before_stalled_release_resumes(self):
        from test_map01_process_identity_backend import backend_fixture, Executor, native
        with backend_fixture() as (backend, events, generation, fake), tempfile.TemporaryDirectory() as root:
            backend.snapshot('source', 0)
            backend.snapshot('current', 0)
            source, current = [row for row in events if row.get('event') == 'observation']
            candidate = action()
            def observed(row, health=97):
                return {'format': 'action-admission-snapshot-v1', 'sequence': row['sequence'],
                    'capture_ns': row['capture_ns'], 'binding': row['pointer_binding'],
                    'signals': {'health': {'status': 'observed', 'value': health}}}
            contract = {'format': CONTRACT_FORMAT,
                'action_fingerprint': action_fingerprint(candidate['commands']),
                'source': {key: value for key, value in observed(source).items() if key != 'format'},
                'max_current_age_ms': 500,
                'predicates': [{'signal_id': 'health', 'operator': 'minimum', 'value': 40}]}
            validity = controller.evaluate_action_validity(candidate['commands'], contract,
                observed(current), time.perf_counter_ns())
            ready = controller.decide_final_admission({'turn_id': 'fixture', 'status': 'completed',
                'answer_eligible': True, 'terminal_observed_ns': source['capture_ns'] - 2},
                None, source['capture_ns'] - 1)
            ready = controller.record_action_validity(ready, candidate['commands'], validity)
            guard = RunningActionGuardV3(candidate, ready, compiler, 'synthetic-fixture-to-x')
            value = program('primary', COMMANDS[:1], [0])
            fake.keysym_to_keycode = lambda sym: 38 if sym == ord('x') else 0
            command = {'op': 'submit', 'id': 'fault', 'steps': value['compiled_steps'],
                'expected_sequence': backend.sequence, 'valid_until_ns': time.perf_counter_ns() + 10_000_000_000}
            incoming, entered, resume = queue.Queue(), threading.Event(), threading.Event()
            sent_ns = time.perf_counter_ns()
            def emit(row):
                events.append(row)
                if row.get('event') == 'accepted':
                    guard.admit_program(value, {'command': command, 'sent_ns': sent_ns},
                        {key: row[key] for key in ('event', 'id', 'steps', 'program_sha256', 'intent_token', 'accepted_ns')})
                    changed = dict(observed(current, 20), sequence=current['sequence'] + 1,
                                   capture_ns=time.perf_counter_ns())
                    guard.check_current(changed, time.perf_counter_ns())
                incoming.put(json.loads(json.dumps(row)))
            executor = Executor(backend, emit)
            original_send = native.xtest.fake_input.side_effect
            def send(connection, event, code):
                if event == native.X.KeyRelease:
                    entered.set()
                    if not resume.wait(5): raise RuntimeError('test release not resumed')
                return original_send(connection, event, code)
            stream = Stream()
            def cancel(text):
                stream.writes.append(text)
                row = json.loads(text)
                self.assertEqual(row, {'op': 'cancel', 'id': 'fault'})
                executor.cancel(row['id'])
            stream.write = cancel
            def wait(predicate):
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    try: row = incoming.get(timeout=max(.001, deadline - time.monotonic()))
                    except queue.Empty: break
                    if predicate(row): return row
                raise TimeoutError('no matching Executor boundary')
            try:
                with patch.object(native.xtest, 'fake_input', side_effect=send):
                    executor.submit('fault', command['steps'], command['expected_sequence'], command['valid_until_ns'])
                    self.assertTrue(entered.wait(1))
                    with self.assertRaises(controller.CancellationReleaseFailed) as caught:
                        controller.cancel_invalidated_action(SimpleNamespace(stdin=stream), wait,
                            'fault', guard, failure_root=root)
                    receipt = caught.exception.receipt
                    self.assertEqual(receipt['reason'], 'terminal_without_release')
                    self.assertEqual(receipt['phase'], 'release')
                    self.assertFalse(receipt['failure_event']['release']['verified'])
                    self.assertEqual(receipt['failure_event']['release_obligation']['intent_token'],
                                     guard.active_intent['intent_token'])
                    self.assertEqual(fake.down, {38})
                    self.assertFalse(resume.is_set())
                    self.assertFalse(backend.owner._inner.stopped.is_set())
                    self.assertFalse(receipt['guard']['current_input_authority'])
                    self.assertTrue(receipt['guard']['physical_input_may_be_down'])
                    saved = json.loads((Path(root) / 'running-cancel-release-failure.json').read_text())
                    self.assertEqual(saved, receipt)
                    print(json.dumps({'stalled_fake_keys': sorted(fake.down),
                        'native_resumed': resume.is_set(), 'receipt': receipt}), flush=True)
            finally:
                resume.set()
                executor.close()

    def test_failure_receipt_is_saved_and_existing_evidence_is_not_overwritten(self):
        values = rows()
        values[1]['event'] = 'input_release_unverified'
        for existing in (False, True):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as root:
                path = Path(root) / 'running-cancel-release-failure.json'
                if existing: path.write_text('original evidence\n')
                with self.assertRaises(controller.CancellationReleaseFailed) as caught:
                    controller.cancel_invalidated_action(SimpleNamespace(stdin=Stream()),
                        waiter(values[:2]), 'p1', armed(), failure_root=root)
                self.assertEqual(caught.exception.receipt['reason'], 'release_unverified')
                if existing:
                    self.assertEqual(path.read_text(), 'original evidence\n')
                    self.assertTrue(any('FileExistsError' in note for note in caught.exception.__notes__))
                else:
                    self.assertEqual(json.loads(path.read_text()), caught.exception.receipt)

    def test_invalid_boundaries_fail_with_original_evidence(self):
        variants = []
        value = rows(); value[0]['matched'] = False; variants.append((value, 'cancel_ack_invalid'))
        value = rows(); value[1]['intent_token'] = 'other'; variants.append((value, 'release_invalid'))
        value = rows(); value[1]['owner_release']['keys_down'] = [38]; variants.append((value, 'release_invalid'))
        value = rows(); value[2]['status'] = 'completed'; variants.append((value, 'terminal_invalid'))
        value = rows(); value[2]['release']['verified'] = False; variants.append((value, 'terminal_invalid'))
        value = rows(); variants.append(([value[0], value[0], value[1]], 'duplicate_cancel_ack'))
        value = rows(); variants.append(([value[0], value[1], value[1]], 'duplicate_release_event'))
        value = rows(); variants.append(([value[2]], 'terminal_before_cancel_ack'))
        value = rows(); variants.append((value[:2], 'boundary_wait_failed'))
        for values, reason in variants:
            with self.subTest(reason=reason), self.assertRaises(controller.CancellationReleaseFailed) as caught:
                controller.cancel_invalidated_action(SimpleNamespace(stdin=Stream()),
                    waiter(values), 'p1', armed())
            self.assertEqual(caught.exception.receipt['reason'], reason)
            self.assertEqual(caught.exception.receipt['observed_boundaries'], values[:len(
                caught.exception.receipt['observed_boundaries'])])
            self.assertFalse(caught.exception.receipt['grants_input_authority'])

    def test_cancel_send_failure_is_not_mistaken_for_release(self):
        stream = Stream()
        def broken(value): raise BrokenPipeError('cancel not delivered')
        stream.write = broken
        with self.assertRaises(controller.CancellationReleaseFailed) as caught:
            controller.cancel_invalidated_action(SimpleNamespace(stdin=stream), waiter([]), 'p1', armed())
        self.assertEqual(caught.exception.receipt['phase'], 'cancel_send')
        self.assertEqual(caught.exception.receipt['error']['type'], 'BrokenPipeError')

    def test_unrelated_failure_cannot_replace_matching_boundary(self):
        values = rows()
        values.insert(0, {'event': 'terminal', 'id': 'other', 'status': 'failed'})
        result = controller.cancel_invalidated_action(SimpleNamespace(stdin=Stream()), waiter(values), 'p1', armed())
        self.assertEqual(result[3]['id'], 'p1')

    def test_failed_terminal_is_not_discarded_waiting_for_success(self):
        values = rows()
        values[2].update(status='failed', release={'verified': False, 'error': 'owner unavailable'})
        with tempfile.TemporaryDirectory() as root:
            try:
                controller.cancel_invalidated_action(SimpleNamespace(stdin=Stream()),
                    waiter([values[0], values[2]]), 'p1', armed())
            except Exception as error:
                receipt = getattr(error, 'receipt', None)
                self.assertIsNotNone(receipt, 'matching failed terminal must become retained failure')
                self.assertEqual(receipt['reason'], 'terminal_without_release')
                self.assertEqual(receipt['failure_event'], values[2])
                self.assertFalse(receipt['grants_input_authority'])
                receipt['failure_event']['release']['verified'] = True
                self.assertFalse(error.receipt['failure_event']['release']['verified'])
            else:
                self.fail('unverified terminal must not succeed')

    def test_unverified_release_does_not_wait_for_later_terminal(self):
        values = rows()
        values[1]['event'] = 'input_release_unverified'
        values[1]['owner_release'].update(verified=False, keys_down=[38])
        try:
            controller.cancel_invalidated_action(SimpleNamespace(stdin=Stream()),
                waiter(values[:2]), 'p1', armed())
        except Exception as error:
            self.assertEqual(getattr(error, 'receipt', {}).get('reason'), 'release_unverified')
        else:
            self.fail('unverified release must not succeed')

    def test_healthy_and_early_release_keep_existing_guard_validation(self):
        for early in (False, True):
            values = rows()
            if early: values = [values[1], values[0], values[2]]
            process = SimpleNamespace(stdin=Stream())
            result = controller.cancel_invalidated_action(process, waiter(values), 'p1', armed())
            self.assertEqual(len(result), 5)
            self.assertEqual(result[4]['state'], 'REVOKED_ACTION_NOT_CURRENT')
            self.assertTrue(result[2]['physical_release_verified'])
            self.assertEqual(json.loads(process.stdin.writes[0]), {'op': 'cancel', 'id': 'p1'})


if __name__ == '__main__':
    unittest.main()
