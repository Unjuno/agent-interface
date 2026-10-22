from __future__ import annotations

import multiprocessing
import time
import unittest

from research.integration.win32_operation_owner_prototype_20261022_r01.operation_owner import (
    InertOperationOwner,
)


def _record(events, count, value):
    with count.get_lock():
        index = count.value
        if index < len(events):
            events[index] = value
        count.value += 1


def blocked_worker(send, request, state, gate, ready, events, count,
                   accept_before_block):
    if accept_before_block:
        state.value = 1
        _record(events, count, 1)
    ready.set()
    gate.wait()
    if not accept_before_block:
        state.value = 1
        _record(events, count, 1)
    send.send({'status': 'operation_finished'})


def silent_worker(send, request, state, ready):
    ready.set()


def release_fake(send, request, state, events, count, succeeds):
    _record(events, count, 2)
    if succeeds:
        state.value = 0
        send.send({'status': 'released'})
    else:
        send.send({'status': 'failed'})


def observe_fake(send, request, state, events, count):
    _record(events, count, 3)
    send.send({'keys_down': ['CTRL'] if state.value else [],
               'buttons_down': []})


def blocked_observer(send, request, state, gate):
    gate.wait()
    send.send({'keys_down': [], 'buttons_down': []})


class NeverRetires:
    def __init__(self, *, target, args, daemon):
        self.target = target
        self.args = args
        self.daemon = daemon
        self.exitcode = None
        self.started = False

    def start(self):
        self.started = True

    def is_alive(self):
        return self.started

    def terminate(self):
        pass

    def join(self, timeout=None):
        pass


class RetiresOnTerminate(NeverRetires):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.terminated = False

    def is_alive(self):
        return self.started and not self.terminated

    def terminate(self):
        self.terminated = True
        self.exitcode = 0


class RecordingRetiringFactory:
    def __init__(self):
        self.created = []

    def __call__(self, *, target, args, daemon):
        self.created.append(target)
        return RetiresOnTerminate(target=target, args=args, daemon=daemon)


class ObserverStallFactory:
    def __init__(self, context):
        self.context = context
        self.created = 0

    def __call__(self, *, target, args, daemon):
        self.created += 1
        if self.created == 3:
            return NeverRetires(target=target, args=args, daemon=daemon)
        return self.context.Process(target=target, args=args, daemon=daemon)


class RecoveryStartFailureFactory:
    def __init__(self, context):
        self.context = context
        self.created = 0

    def __call__(self, *, target, args, daemon):
        self.created += 1
        if self.created == 2:
            raise OSError('injected recovery worker start failure')
        return self.context.Process(target=target, args=args, daemon=daemon)


class InertOperationOwnerTests(unittest.TestCase):
    def setUp(self):
        self.ctx = multiprocessing.get_context('spawn')
        self.state = self.ctx.Value('i', 0)
        self.gate = self.ctx.Event()
        self.ready = self.ctx.Event()
        self.events = self.ctx.Array('i', 8)
        self.event_count = self.ctx.Value('i', 0)
        self.owner = self._owner()
        self.request = {'operation_id': 'op-1', 'session_id': 'session-1',
                        'target_generation': 7, 'keys': ['CTRL'],
                        'buttons': []}

    def _owner(self, *, accept_before_block=True, recovery_succeeds=True,
               observer=observe_fake, process_factory=None, worker=blocked_worker):
        return InertOperationOwner(
            worker, release_fake, observer,
            worker_args=(self.state, self.gate, self.ready, self.events,
                         self.event_count, accept_before_block),
            recovery_args=(self.state, self.events, self.event_count,
                           recovery_succeeds),
            observer_args=(self.state, self.events, self.event_count),
            context=self.ctx, process_factory=process_factory)

    def _begin(self, request=None):
        result = self.owner.begin(
            request or self.request, current_session_id='session-1',
            current_target_generation=7)
        self.assertEqual(result['status'], 'admitted', result)
        self.assertTrue(self.ready.wait(2))

    def _cancel(self, operation_id='op-1', seconds=3):
        return self.owner.cancel(
            operation_id,
            deadline_monotonic_ns=time.monotonic_ns() + int(seconds * 1e9))

    def test_accepted_then_blocked_retires_before_fake_up_and_readback(self):
        self._begin()
        self.assertEqual(self.state.value, 1)
        result = self._cancel()
        self.assertEqual(result['status'], 'input_recovered_fake', result)
        self.assertTrue(result['producer_retired'])
        self.assertTrue(result['synthetic_neutral_state'])
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])
        self.assertEqual(result['operation_result'], 'unknown')
        self.assertEqual(list(self.events[:self.event_count.value]), [1, 2, 3])

    def test_blocked_before_acceptance_cannot_emit_down_after_retirement(self):
        self.owner = self._owner(accept_before_block=False)
        self._begin()
        self.assertEqual(self.state.value, 0)
        result = self._cancel()
        self.assertEqual(result['status'], 'input_recovered_fake', result)
        time.sleep(0.05)
        self.assertEqual(self.state.value, 0)
        self.assertEqual(list(self.events[:self.event_count.value]), [2, 3])

    def test_no_overlapping_dispatch_and_stale_operation_refused(self):
        self._begin()
        second = dict(self.request, operation_id='op-2')
        busy = self.owner.begin(second, current_session_id='session-1',
                                current_target_generation=7)
        self.assertEqual(busy['reason'], 'producer_not_retired')
        stale = self._cancel('op-old')
        self.assertEqual(stale['reason'], 'stale_operation_id')
        self.assertEqual(self._cancel()['status'], 'input_recovered_fake')

    def test_repeated_cancel_is_idempotent_and_never_replays(self):
        self._begin()
        first = self._cancel()
        second = self._cancel()
        self.assertEqual(first['status'], 'input_recovered_fake')
        self.assertTrue(second['duplicate'])
        self.assertEqual(self.event_count.value, 3)

    def test_unconfirmed_retirement_fences_without_release(self):
        owner = self._owner(process_factory=NeverRetires)
        self.owner = owner
        result = owner.begin(self.request, current_session_id='session-1',
                             current_target_generation=7)
        self.assertEqual(result['status'], 'admitted')
        cancelled = self._cancel(seconds=0.02)
        self.assertEqual(cancelled['status'], 'unknown')
        self.assertFalse(cancelled['producer_retired'])
        self.assertFalse(cancelled['recovery_attempted'])
        self.assertEqual(self.event_count.value, 0)
        second = dict(self.request, operation_id='op-2')
        refused = owner.begin(second, current_session_id='session-1',
                              current_target_generation=7)
        self.assertEqual(refused['reason'], 'producer_not_retired')

    def test_recovery_failure_never_runs_observer_or_claims_release(self):
        self.owner = self._owner(recovery_succeeds=False)
        self._begin()
        result = self._cancel()
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason'], 'recovery_unconfirmed')
        self.assertEqual(self.event_count.value, 2)
        self.assertFalse(result['replay_allowed'])

    def test_fresh_generation_is_required_after_recovery(self):
        self._begin()
        self.assertEqual(self._cancel()['status'], 'input_recovered_fake')
        same = dict(self.request, operation_id='op-2')
        refused = self.owner.begin(same, current_session_id='session-1',
                                   current_target_generation=7)
        self.assertEqual(refused['reason'], 'fresh_target_required')
        fresh = dict(self.request, operation_id='op-3',
                     target_generation=8)
        admitted = self.owner.begin(fresh, current_session_id='session-1',
                                    current_target_generation=8)
        self.assertEqual(admitted['status'], 'admitted')
        self.assertEqual(self._cancel('op-3')['status'], 'input_recovered_fake')

    def test_generation_mismatch_refuses_before_process_start(self):
        stale = self.owner.begin(self.request, current_session_id='session-1',
                                 current_target_generation=8)
        self.assertEqual(stale['reason'], 'stale_target_generation')
        self.assertEqual(self.event_count.value, 0)

    def test_missing_operation_receipt_keeps_task_unknown(self):
        self.owner = InertOperationOwner(
            silent_worker, release_fake, observe_fake,
            worker_args=(self.state, self.ready),
            recovery_args=(self.state, self.events, self.event_count, True),
            observer_args=(self.state, self.events, self.event_count),
            context=self.ctx)
        self._begin()
        result = self._cancel()
        self.assertEqual(result['status'], 'input_recovered_fake')
        self.assertEqual(result['operation_result'], 'unknown')
        self.assertIsNone(result['task_success'])
        self.assertFalse(result['replay_allowed'])

    def test_expired_budget_does_not_start_recovery_process(self):
        factory = RecordingRetiringFactory()
        self.owner = self._owner(process_factory=factory)
        admitted = self.owner.begin(self.request, current_session_id='session-1',
                                    current_target_generation=7)
        self.assertEqual(admitted['status'], 'admitted')
        cancelled = self.owner.cancel(
            'op-1', deadline_monotonic_ns=time.monotonic_ns())
        self.assertEqual(cancelled['status'], 'unknown')
        self.assertEqual(cancelled['reason'], 'deadline_expired_before_recovery')
        self.assertFalse(cancelled['recovery_attempted'])
        self.assertEqual(len(factory.created), 1)

    def test_observer_retirement_timeout_preserves_unknown(self):
        factory = ObserverStallFactory(self.ctx)
        self.owner = InertOperationOwner(
            blocked_worker, release_fake, blocked_observer,
            worker_args=(self.state, self.gate, self.ready, self.events,
                         self.event_count, True),
            recovery_args=(self.state, self.events, self.event_count, True),
            observer_args=(self.state, self.gate),
            context=self.ctx, process_factory=factory)
        self._begin()
        started = time.monotonic()
        result = self._cancel(seconds=3)
        elapsed = time.monotonic() - started
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason'], 'neutral_state_unconfirmed')
        self.assertEqual(result['observation']['reason'], 'helper_not_retired')
        self.assertLess(elapsed, 3.5)
        self.assertFalse(result['replay_allowed'])

    def test_recovery_process_start_failure_keeps_input_fenced(self):
        factory = RecoveryStartFailureFactory(self.ctx)
        self.owner = self._owner(process_factory=factory)
        self._begin()
        result = self._cancel()
        self.assertEqual(result['status'], 'unknown')
        self.assertEqual(result['reason'], 'recovery_unconfirmed')
        self.assertEqual(result['recovery']['reason'],
                         'helper_start_or_run_failed')
        self.assertTrue(result['producer_retired'])
        self.assertFalse(result['replay_allowed'])
        self.assertEqual(self.event_count.value, 0)


if __name__ == '__main__':
    unittest.main()
