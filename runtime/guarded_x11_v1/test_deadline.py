"""Deterministic expiry controls; no display, input, or real sleeps."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from runtime.backends.x11_v1.backend import X11Backend, X11BackendError, X11ExecutionError
from runtime.guarded_x11_v1.bridge import _GuardedBackend


class DeadlineTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_000_000
        self.backend = object.__new__(_GuardedBackend)
        self.backend.owner = SimpleNamespace(active=('field',[0,0]), deadline=11_000_000)
        self.backend.emissions = 0
        self.backend.preflight = Mock()
        self.backend.text = Mock()
        self.backend.release_all = Mock(return_value={
            'verified':True, 'keys_down':[], 'buttons_down':[]})
        clock = patch('time.monotonic_ns', side_effect=lambda:self.now)
        clock.start(); self.addCleanup(clock.stop)
        sleeper = patch('time.sleep', side_effect=self.advance)
        self.sleep = sleeper.start(); self.addCleanup(sleeper.stop)

    def advance(self, seconds):
        self.now += round(seconds*1_000_000_000)

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


if __name__ == '__main__': unittest.main()
