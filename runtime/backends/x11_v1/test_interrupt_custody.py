"""Actual session/execute methods; memory-only input, no native X connection."""
import unittest
import json
from unittest.mock import Mock, patch
from types import SimpleNamespace
from Xlib import X

from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.cli_v1.api import dispatch_in_session
from runtime.core_v1.contract import OFFICE_FLOOR, capability_manifest
from runtime.core_v1.test_contract import program


class InterruptCustodyTests(unittest.TestCase):
    def backend(self, interrupt, cleanup=None):
        b = object.__new__(X11Backend)
        b.emissions = 0
        b.held_keycodes = {}
        b.held_buttons = set()
        b.preflight = Mock()
        b._refresh_keyboard_mapping = Mock(return_value=False)
        b.d = Mock()
        b.root = Mock()
        b.root.query_pointer.return_value = SimpleNamespace(mask=0)
        b._keycode = Mock(return_value=38)
        physical = set()
        def emit(connection, kind, code):
            self.assertIs(connection, b.d)
            if kind == X.KeyPress:
                physical.add(code)
            elif kind == X.KeyRelease:
                physical.discard(code)
            else:
                self.fail('unexpected input type')
        def keymap():
            bits = bytearray(32)
            for code in physical:
                bits[code // 8] |= 1 << (code % 8)
            return bits
        b.d.query_keymap.side_effect = keymap
        b.fake_physical = physical
        self.enterContext(patch('runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=emit))
        self.enterContext(patch('runtime.backends.x11_v1.backend.display.Display',
                                side_effect=AssertionError('native display forbidden')))
        b.monotonic_ns = lambda: 9000
        b.manifest = lambda: capability_manifest('inert', 'linux', 'x11', OFFICE_FLOOR)
        b.close = Mock()
        def text(value):
            b.key_state('a', True)
            if interrupt is not None:
                raise interrupt
        b.text = Mock(side_effect=text)
        def release():
            if cleanup is not None:
                raise cleanup
            return X11Backend.release_all(b)
        b.release_all = Mock(side_effect=release)
        return b

    def dispatch(self, session):
        p = program()
        p['ops'] = [{'op': 'text', 'text': 'a'}, {'op': 'release_all'}]
        return dispatch_in_session(session, p, current_observation_seq=7,
                                   current_binding_revision=3)

    def test_primary_interrupt_survives_cleanup_and_quarantines(self):
        for exception in (KeyboardInterrupt, SystemExit):
            for cleanup in (None, OSError('cleanup failed'), SystemExit('cleanup interrupted')):
                with self.subTest(exception=exception.__name__, cleanup=type(cleanup).__name__):
                    original = exception('during input')
                    b = self.backend(original, cleanup)
                    session = X11RuntimeSession(b)
                    with self.assertRaises(exception) as caught:
                        self.dispatch(session)
                    self.assertIs(caught.exception, original)
                    b.release_all.assert_called_once()
                    self.assertTrue(session.recovery_required)
                    self.assertEqual(session.dispatch(program(), current_observation_seq=7,
                                                     current_binding_revision=3)['error'], 'INPUT_RECOVERY_REQUIRED')
                    evidence = b.interrupted_execution
                    self.assertEqual(evidence['failed_op'], 0)
                    self.assertEqual(evidence['completed_ops'], [])
                    self.assertIn('during input', evidence['error'])
                    self.assertEqual(evidence['releases'][0]['verified'], cleanup is None)
                    self.assertEqual(b.held_keycodes, {} if cleanup is None else {'a': 38})
                    self.assertEqual(b.fake_physical, set() if cleanup is None else {38})
                    b.close.assert_not_called()
                    print(json.dumps({'case': 'primary-interrupt', 'interrupt': type(original).__name__,
                        'cleanup_interrupt': type(cleanup).__name__, 'quarantine': session.recovery_required,
                        'held_keycodes': dict(b.held_keycodes), 'fake_down': sorted(b.fake_physical),
                        'execution': evidence}), flush=True)
                    b.release_all.side_effect = lambda: X11Backend.release_all(b)
                    self.assertEqual(session.recover_input()['status'], 'input_recovered')
                    self.assertFalse(session.recovery_required)
                    self.assertEqual(b.fake_physical, set())
                    self.assertIs(b.interrupted_execution, evidence)
                    b.text.assert_called_once_with('a')
                    print(json.dumps({'case': 'explicit-recovery', 'interrupt': type(original).__name__,
                        'cleanup_interrupt': type(cleanup).__name__, 'quarantine': session.recovery_required,
                        'held_keycodes': dict(b.held_keycodes), 'fake_down': sorted(b.fake_physical),
                        'text_calls': b.text.call_count}), flush=True)

    def test_cleanup_interrupt_propagates_instead_of_ordinary_failure(self):
        original, cleanup = OSError('input failed'), KeyboardInterrupt('cleanup interrupted')
        b = self.backend(original, cleanup)
        session = X11RuntimeSession(b)
        with self.assertRaises(KeyboardInterrupt) as caught:
            self.dispatch(session)
        self.assertIs(caught.exception, cleanup)
        self.assertIs(cleanup.__cause__, original)
        self.assertTrue(session.recovery_required)
        self.assertIn('input failed', b.interrupted_execution['error'])
        self.assertFalse(b.interrupted_execution['releases'][0]['verified'])

    def test_recovery_interrupt_retains_quarantine_then_explicit_release_only(self):
        b = self.backend(None)
        session = X11RuntimeSession(b)
        session.recovery_required = True
        original = KeyboardInterrupt('during recovery')
        b.release_all.side_effect = original
        with self.assertRaises(KeyboardInterrupt) as caught:
            session.recover_input()
        self.assertIs(caught.exception, original)
        self.assertTrue(session.recovery_required)
        b.release_all.side_effect = None
        b.release_all.return_value = {'verified': True, 'keys_down': [], 'buttons_down': []}
        self.assertEqual(session.recover_input()['status'], 'input_recovered')
        b.text.assert_not_called()

    def test_interrupted_preflight_cleanup_also_retains_quarantine(self):
        from runtime.backends.x11_v1.backend import X11BackendError
        for second in (False, True):
            with self.subTest(second_preflight=second):
                b = self.backend(None)
                b.preflight.side_effect = ([None] if second else []) + [X11BackendError('preflight')]
                b.release_all.side_effect = KeyboardInterrupt('cleanup')
                session = X11RuntimeSession(b)
                with self.assertRaises(KeyboardInterrupt):
                    self.dispatch(session)
                self.assertTrue(session.recovery_required)
                b.text.assert_not_called()

    def test_preflight_interrupt_quarantines_without_starting_input(self):
        b = self.backend(None)
        original = KeyboardInterrupt('preflight query')
        b.preflight.side_effect = original
        session = X11RuntimeSession(b)
        with self.assertRaises(KeyboardInterrupt) as caught:
            self.dispatch(session)
        self.assertIs(caught.exception, original)
        self.assertTrue(session.recovery_required)
        b.text.assert_not_called()
        b.release_all.assert_not_called()

    def test_healthy_program_still_dispatches_and_verifies(self):
        b = self.backend(None)
        session = X11RuntimeSession(b)
        row = self.dispatch(session)
        self.assertEqual(row['result']['status'], 'completed')
        self.assertFalse(session.recovery_required)
        self.assertEqual(b.fake_physical, set())
        self.assertEqual(b.emissions, 2)
        b.text.assert_called_once_with('a')


if __name__ == '__main__':
    unittest.main()
