"""Deterministic expiry controls; no display, input, or real sleeps."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from runtime.backends.x11_v1.backend import X11Backend, X11BackendError, X11ExecutionError
from runtime.guarded_x11_v1.bridge import _GuardedBackend, NativeHandleBridge


class DeadlineTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_000_000
        self.backend = object.__new__(_GuardedBackend)
        self.backend.owner = SimpleNamespace(active=('field',[0,0]), deadline=11_000_000)
        self.backend.owner._focus_within_target = Mock(return_value=True)
        self.backend.emissions = 0
        self.backend.preflight = Mock()
        # This fixture isolates expiry at physical emission, without an X server.
        self.backend._refresh_keyboard_mapping = Mock(return_value=False)
        self.backend.text = Mock()
        self.backend.release_all = Mock(return_value={
            'verified':True, 'keys_down':[], 'buttons_down':[]})
        clock = patch('time.monotonic_ns', side_effect=lambda:self.now)
        clock.start(); self.addCleanup(clock.stop)
        sleeper = patch('time.sleep', side_effect=self.advance)
        self.sleep = sleeper.start(); self.addCleanup(sleeper.stop)

    def advance(self, seconds):
        self.now += round(seconds*1_000_000_000)

    def test_focus_loss_before_press_refuses_but_release_is_allowed(self):
        self.backend.owner._focus_within_target.return_value = False
        with patch.object(X11Backend, 'key_state') as emit:
            with self.assertRaisesRegex(X11BackendError, 'focus.*outside'):
                self.backend.key_state('a', True)
            emit.assert_not_called()
            self.backend.key_state('CTRL', False)
            emit.assert_called_once_with('CTRL', False)

    def test_focus_loss_after_modifier_releases_without_following_key(self):
        emitted = []
        def emit(key, down):
            emitted.append((key, down))
            self.backend.owner._focus_within_target.return_value = False
        with patch.object(X11Backend, 'key_state', side_effect=emit):
            with self.assertRaises(X11ExecutionError) as caught:
                self.backend.execute({'ops':[{'op':'key_chord','keys':['CTRL','a']},
                                            {'op':'text','text':'must-not-run'}]})
        self.assertEqual(emitted, [('CTRL', True)])
        self.assertEqual(caught.exception.execution['failed_op'], 0)
        self.backend.release_all.assert_called_once()
        self.backend.text.assert_not_called()

    def test_wait_expires_releases_and_never_starts_tail(self):
        with self.assertRaises(X11ExecutionError) as caught:
            self.backend.execute({'ops':[{'op':'wait_update','timeout_ms':25},
                {'op':'text','text':'must-not-run'}, {'op':'release_all'}]})
        evidence = caught.exception.execution
        self.assertEqual(self.now, 11_000_000)
        self.assertEqual(evidence['failed_op'], 0)
        self.assertEqual(evidence['completed_ops'], [])
        self.assertFalse(evidence['waits'][0]['completed'])
        self.assertEqual(evidence['waits'][0]['requested_ms'], 25)
        self.assertIsNone(evidence['waits'][0]['update_observed'])
        self.assertTrue(evidence['releases'][0]['verified'])
        self.backend.text.assert_not_called()
        self.backend.release_all.assert_called_once()

    def test_short_wait_completes_without_renewing_deadline(self):
        self.backend._wait_update(3)
        self.assertEqual(self.now, 4_000_000)
        self.assertEqual(self.backend.owner.deadline, 11_000_000)
        self.backend._wait_update(0)
        self.assertEqual(self.now, 4_000_000)

    def test_early_wake_does_not_turn_partial_wait_into_completed(self):
        self.sleep.side_effect = lambda seconds:self.advance(min(seconds,.002))
        with self.assertRaisesRegex(X11BackendError, 'expired during wait'):
            self.backend._wait_update(25)
        self.assertEqual(self.now, 11_000_000)
        self.assertEqual(self.sleep.call_count, 5)

    def test_expired_press_refuses_but_key_release_remains_allowed(self):
        self.now = 11_000_000
        with patch.object(X11Backend, 'key_state') as emit:
            with self.assertRaisesRegex(X11BackendError, 'expired'):
                self.backend.key_state('a', True)
            emit.assert_not_called()
            self.backend.key_state('SHIFT', False)
            emit.assert_called_once_with('SHIFT', False)

    def test_chord_expiry_after_modifier_releases_prefix_without_next_press(self):
        emitted = []
        def emit(key, down):
            emitted.append((key,down)); self.now = 11_000_000
        with patch.object(X11Backend, 'key_state', side_effect=emit):
            with self.assertRaises(X11ExecutionError) as caught:
                self.backend.execute({'ops':[{'op':'key_chord','keys':['CTRL','a']},
                                             {'op':'text','text':'must-not-run'}]})
        self.assertEqual(emitted, [('CTRL',True)])
        self.assertEqual(caught.exception.execution['failed_op'], 0)
        self.backend.release_all.assert_called_once()
        self.backend.text.assert_not_called()

    def test_inactive_guard_keeps_base_delay(self):
        self.backend.owner.active = None
        self.backend._wait_update(25)
        self.sleep.assert_called_once_with(.025)
        self.assertEqual(self.now, 26_000_000)

    def test_release_failure_is_retained_after_expiry(self):
        self.backend.release_all.side_effect = OSError('release failed')
        self.now = 11_000_000
        with self.assertRaises(X11ExecutionError) as caught:
            self.backend.execute({'ops':[{'op':'wait_update','timeout_ms':0}]})
        self.assertFalse(caught.exception.execution['releases'][0]['verified'])
        self.assertIn('release failed', caught.exception.execution['releases'][0]['error'])


class CallerDeadlineTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_000_000
        self.bridge = object.__new__(NativeHandleBridge)
        self.bridge.active = None
        self.bridge.session = SimpleNamespace(recovery_required=False)
        self.bridge.review_required = False
        self.bridge.sequence = 7
        self.bridge.binding_revision = 2
        self.bridge.scope = 'deadline:test'
        self.bridge.target = 'app'
        self.bridge._save = Mock()
        self.bridge.check = Mock(return_value={'point': [20, 30]})
        clock = patch('time.monotonic_ns', side_effect=lambda:self.now)
        clock.start(); self.addCleanup(clock.stop)
        dispatcher = patch('runtime.guarded_x11_v1.bridge.dispatch_in_session')
        self.dispatch = dispatcher.start(); self.addCleanup(dispatcher.stop)
        self.dispatch.return_value = {'status': 'returned', 'result': {'status': 'completed'}}

    def invoke(self, interaction, expires):
        tail = [{'op':'text', 'text':'a'}] if interaction == 'keyboard' else []
        return getattr(self.bridge, interaction)('field', [0,0], tail=tail, expires_at_ns=expires)

    def test_shorter_caller_deadline_reaches_program_and_backend_guard(self):
        for interaction in ('click', 'move', 'keyboard'):
            with self.subTest(interaction=interaction):
                self.bridge.check.side_effect = lambda stage: (
                    self.assertEqual(self.bridge.deadline, 11_000_000) or {'point':[20,30]})
                self.invoke(interaction, 11_000_000)
                program = self.dispatch.call_args.args[1]
                self.assertEqual(program['authority']['expires_at_ns'], 11_000_000)
                self.assertIsNone(self.bridge.active)
                self.assertIsNone(self.bridge.deadline)

    def test_caller_cannot_extend_existing_five_second_cap(self):
        self.invoke('click', 10_000_000_000)
        self.assertEqual(self.dispatch.call_args.args[1]['authority']['expires_at_ns'],
                         self.now + 5_000_000_000)

    def test_expired_caller_deadline_refuses_before_capture_or_dispatch(self):
        for expires in (self.now - 1, self.now):
            with self.subTest(expires=expires):
                row = self.invoke('click', expires)
                self.assertEqual(row['status'], 'refused')
                self.assertEqual(row['error'], 'CALLER_DEADLINE_EXPIRED')
                self.assertFalse(row['input_dispatched'])
        self.bridge.check.assert_not_called()
        self.dispatch.assert_not_called()
        self.assertIsNone(self.bridge.active)

    def test_invalid_deadline_does_not_activate_guard(self):
        for expires in (True, 0, -1, 1.5, '10000000'):
            with self.subTest(expires=expires), self.assertRaises(ValueError):
                self.invoke('click', expires)
        self.bridge.check.assert_not_called()
        self.dispatch.assert_not_called()
        self.assertIsNone(self.bridge.active)

    def test_no_deadline_preserves_existing_five_second_cap(self):
        self.bridge.click('field', [0,0])
        self.assertEqual(self.dispatch.call_args.args[1]['authority']['expires_at_ns'],
                         self.now + 5_000_000_000)

    def test_capture_cost_cannot_leave_dispatch_with_expired_authority(self):
        def capture(stage):
            self.now = 11_000_000
            return {'point':[20,30]}
        self.bridge.check.side_effect = capture
        row = self.invoke('click', 11_000_000)
        self.assertEqual(row['status'], 'refused')
        self.assertFalse(row['input_dispatched'])
        self.dispatch.assert_not_called()
        self.assertIsNone(self.bridge.active)
        self.assertIsNone(self.bridge.deadline)


if __name__ == '__main__': unittest.main()
