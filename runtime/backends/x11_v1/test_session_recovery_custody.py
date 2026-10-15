"""Serialized same-backend session replacement at actual inert X boundaries."""
import json
import unittest
from unittest.mock import Mock

from runtime.backends.x11_v1 import test_held_preflight as fixtures
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.cli_v1.api import dispatch_in_session


class SessionRecoveryCustodyTests(unittest.TestCase):
    def fixture(self):
        f = fixtures.HeldPreflightTests()
        f.setUp()
        self.addCleanup(f.doCleanups)
        f.backend._activation_supported = Mock(return_value=False)
        return f

    def dispatch(self, session, f, ops):
        return dispatch_in_session(session, f.program(ops), current_observation_seq=0,
                                   current_binding_revision=0)['result']

    def fail_release(self, f, session, *, held=True):
        actual_release = f.backend.release_all
        f.backend.release_all = Mock(side_effect=OSError('release unavailable'))
        row = self.dispatch(session, f, [{'op': 'key_state', 'key': 'a', 'down': True}] if held else [])
        self.assertEqual(row['status'], 'execution_failed')
        self.assertTrue(session.recovery_required)
        return actual_release, row

    def test_new_and_preexisting_wrappers_cannot_dispatch_during_failed_release(self):
        for preexisting in (False, True):
            with self.subTest(preexisting=preexisting):
                f = self.fixture()
                first = X11RuntimeSession(f.backend)
                other = X11RuntimeSession(f.backend) if preexisting else None
                _, failed = self.fail_release(f, first)
                if other is None:
                    other = X11RuntimeSession(f.backend)
                before = list(f.events)
                row = self.dispatch(other, f, [{'op': 'text', 'text': 'b'}])
                print(json.dumps({'case': 'replacement', 'preexisting': preexisting,
                    'original': failed, 'replacement': row, 'before': before, 'after': f.events,
                    'fake_down': sorted(f.physical), 'held': f.backend.held_keycodes}), flush=True)
                self.assertEqual(row['status'], 'refused')
                self.assertEqual(row['error'], 'INPUT_RECOVERY_REQUIRED')
                self.assertEqual(f.events, before)
                self.assertEqual(f.physical, {38})
                self.assertTrue(first.recovery_required)
                self.assertTrue(other.recovery_required)

    def test_empty_ledger_does_not_erase_failed_release_evidence(self):
        f = self.fixture()
        first = X11RuntimeSession(f.backend)
        self.fail_release(f, first, held=False)
        self.assertEqual(f.backend.held_keycodes, {})
        replacement = X11RuntimeSession(f.backend)
        before = list(f.events)
        row = self.dispatch(replacement, f, [{'op': 'text', 'text': 'b'}])
        self.assertEqual(row['error'], 'INPUT_RECOVERY_REQUIRED')
        self.assertEqual(f.events, before)

    def test_direct_cleanup_does_not_reset_and_each_old_wrapper_acknowledges_recovery(self):
        f = self.fixture()
        first, other = X11RuntimeSession(f.backend), X11RuntimeSession(f.backend)
        actual_release, failed = self.fail_release(f, first)
        f.backend.release_all.side_effect = actual_release
        self.assertTrue(f.backend.release_all()['verified'])
        self.assertEqual(f.physical, set())
        replacement = X11RuntimeSession(f.backend)
        for session in (first, other, replacement):
            self.assertTrue(session.recovery_required)
        before = list(f.events)
        recovery = other.recover_input()
        self.assertEqual(recovery['status'], 'input_recovered')
        self.assertEqual(f.events, before)
        self.assertFalse(other.recovery_required)
        self.assertFalse(replacement.recovery_required)
        self.assertTrue(first.recovery_required)
        self.assertEqual(first.recover_input()['status'], 'input_recovered')
        self.assertFalse(first.recovery_required)
        self.assertFalse(other.recovery_required)
        chosen = self.dispatch(replacement, f, [{'op': 'text', 'text': 'b'}])
        self.assertEqual(chosen['status'], 'completed')
        print(json.dumps({'case': 'explicit-recovery', 'original': failed, 'recovery': recovery,
                          'chosen': chosen, 'events': f.events}), flush=True)

    def test_failed_and_interrupted_recovery_remain_shared(self):
        for interruption in (OSError, KeyboardInterrupt):
            with self.subTest(interruption=interruption.__name__):
                f = self.fixture()
                first, other = X11RuntimeSession(f.backend), X11RuntimeSession(f.backend)
                self.fail_release(f, first)
                f.backend.release_all.side_effect = interruption('recovery interrupted')
                if interruption is KeyboardInterrupt:
                    with self.assertRaises(KeyboardInterrupt):
                        other.recover_input()
                else:
                    self.assertEqual(other.recover_input()['status'], 'recovery_failed')
                self.assertTrue(first.recovery_required)
                self.assertTrue(other.recovery_required)
                self.assertTrue(X11RuntimeSession(f.backend).recovery_required)

    def test_healthy_replacement_remains_usable(self):
        f = self.fixture()
        first, other = X11RuntimeSession(f.backend), X11RuntimeSession(f.backend)
        for session in (first, other, X11RuntimeSession(f.backend)):
            row = self.dispatch(session, f, [{'op': 'text', 'text': 'b'}])
            self.assertEqual(row['status'], 'completed')
            self.assertFalse(session.recovery_required)
        self.assertEqual(f.physical, set())

    def test_assigning_false_cannot_clear_backend_or_wrapper_obligation(self):
        f = self.fixture()
        session = X11RuntimeSession(f.backend)
        actual_release, _ = self.fail_release(f, session)
        with self.assertRaisesRegex(ValueError, 'explicit verified'):
            session.recovery_required = False
        f.backend.release_all.side_effect = actual_release
        replacement = X11RuntimeSession(f.backend)
        self.assertEqual(replacement.recover_input()['status'], 'input_recovered')
        with self.assertRaisesRegex(ValueError, 'explicit verified'):
            session.recovery_required = False
        self.assertTrue(session.recovery_required)


if __name__ == '__main__':
    unittest.main()
