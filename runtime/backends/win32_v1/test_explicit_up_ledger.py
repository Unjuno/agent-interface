"""Actual Win32 method/session regressions with inert endpoints only."""
import json
import unittest
from unittest.mock import patch

from runtime.backends.win32_v1 import backend as native
from runtime.backends.win32_v1.session import Win32RuntimeSession
from runtime.core_v1.contract import SCHEMA_PROGRAM


class InputState:
    def __init__(self, stubborn=False, *, send_error=False, query_error=False):
        self.down = set()
        self.stubborn = stubborn
        self.send_error = send_error
        self.query_error = query_error
        self.events = []

    def SendInput(self, count, items, size):
        if count != 1:
            raise AssertionError('only single inert inputs allowed')
        item = items[0]
        if item.type == native.INPUT_KEYBOARD:
            vk = int(item.ki.wVk)
            down = not bool(item.ki.dwFlags & native.KEYEVENTF_KEYUP)
        elif item.type == native.INPUT_MOUSE:
            matches = [(vk, bool(item.mi.dwFlags & down_flag))
                       for down_flag, up_flag, vk in native.BUTTON_FLAGS.values()
                       if item.mi.dwFlags in (down_flag, up_flag)]
            if len(matches) != 1:
                raise AssertionError('only known inert button inputs allowed')
            vk, down = matches[0]
        else:
            raise AssertionError('unknown inert input')
        self.events.append({'send': vk, 'down': down})
        if self.send_error:
            raise native.Win32BackendError('inert send unavailable')
        if down:
            self.down.add(vk)
        elif not self.stubborn:
            self.down.discard(vk)
        return 1

    def GetAsyncKeyState(self, vk):
        self.events.append({'query': vk})
        if self.query_error:
            raise RuntimeError('inert read unavailable')
        return 0x8000 if vk in self.down else 0


class ExplicitUpLedgerTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(native.Win32Backend, '__init__',
                                      side_effect=AssertionError('constructor forbidden')))
        self.enterContext(patch.object(native.ctypes, 'WinDLL', create=True,
                                      side_effect=AssertionError('WinDLL forbidden')))
        self.enterContext(patch.object(native.time, 'sleep', return_value=None))
        self.enterContext(patch.object(native.time, 'monotonic_ns', return_value=123456))

    def backend(self, **options):
        obj = native.Win32Backend.__new__(native.Win32Backend)
        obj.held_keys = {}
        obj.held_buttons = set()
        obj.emissions = 0
        obj.user32 = InputState(**options)
        return obj

    def record(self, obj, case, call):
        try:
            value = call()
        except Exception as error:
            value = {'exception': type(error).__name__, 'detail': str(error)}
            self.emit(obj, case, value)
            raise
        self.emit(obj, case, value)
        return value

    def emit(self, obj, case, value):
        print(json.dumps({'test': self.id(), 'case': case, 'value': value,
                          'held_keys': obj.held_keys, 'held_buttons': sorted(obj.held_buttons),
                          'api_down': sorted(obj.user32.down), 'events': obj.user32.events,
                          'emissions': obj.emissions}, sort_keys=True))

    def dispatch(self, obj, case, ops):
        program = {'schema': SCHEMA_PROGRAM, 'program_id': case,
                   'source': {'observation_seq': 7, 'binding_revision': 3},
                   'authority': {'lease_id': 'ordinary-explicit-up', 'expires_at_ns': 100},
                   'terminal': {'release_all_required': True},
                   'ops': ops + [{'op': 'release_all'}]}
        return Win32RuntimeSession(obj).dispatch(program, current_observation_seq=7,
                                                 current_binding_revision=3, now_ns=1)

    def family(self, name, ops, vk, *, key=None, button=None):
        for stubborn in (False, True):
            with self.subTest(stubborn=stubborn):
                obj = self.backend(stubborn=stubborn)
                reply = self.record(obj, name + ('_stubborn' if stubborn else '_healthy'),
                                    lambda: self.dispatch(obj, name, ops))
                if stubborn:
                    self.assertEqual(reply['status'], 'execution_failed')
                    self.assertEqual(reply['error'], 'BACKEND_EXECUTION')
                    release = reply['release']
                else:
                    self.assertEqual(reply['admission'], 'accepted')
                    release = reply['execution']['releases'][-1]
                self.assertIs(release['verified'], not stubborn)
                self.assertEqual(reply['status'], 'execution_failed' if stubborn else 'completed')
                self.assertEqual(obj.user32.down, {vk} if stubborn else set())
                self.assertEqual(obj.held_keys, {key: vk} if stubborn and key else {})
                self.assertEqual(obj.held_buttons, {button} if stubborn and button else set())
                if stubborn:
                    self.assertEqual(release['keys_down'], [key] if key else [])
                    self.assertEqual(release['buttons_down'], [button] if button else [])

    def test_key_pair_terminal_rejects_reported_down_input(self):
        self.family('key_pair', [{'op': 'key_state', 'key': 'Q', 'down': True},
                                 {'op': 'key_state', 'key': 'Q', 'down': False}], 81, key='Q')

    def test_button_pair_terminal_rejects_reported_down_input(self):
        self.family('button_pair', [{'op': 'pointer_button', 'button': 'left', 'down': True},
                                    {'op': 'pointer_button', 'button': 'left', 'down': False}], 1, button='left')

    def test_chord_terminal_rejects_reported_down_input(self):
        self.family('chord', [{'op': 'key_chord', 'keys': ['Q']}], 81, key='Q')

    def test_untracked_up_does_not_claim_unowned_inputs(self):
        obj = self.backend(stubborn=True)
        obj.user32.down = {81, 1}
        with self.assertRaisesRegex(native.Win32BackendError, 'key UP unverified'):
            obj.key_state('Q', False)
        with self.assertRaisesRegex(native.Win32BackendError, 'button UP unverified'):
            obj.pointer_button('left', False)
        release = self.record(obj, 'untracked_control', obj.release_all)
        self.assertIs(release['verified'], True)
        self.assertEqual(obj.held_keys, {})
        self.assertEqual(obj.held_buttons, set())
        self.assertEqual(obj.user32.down, {81, 1})
        self.assertTrue(any('query' in event for event in obj.user32.events))

    def test_explicit_up_send_failure_preserves_existing_obligation(self):
        for name in ('key', 'button'):
            with self.subTest(name=name):
                obj = self.backend()
                down = (lambda: obj.key_state('Q', True)) if name == 'key' else (lambda: obj.pointer_button('left', True))
                up = (lambda: obj.key_state('Q', False)) if name == 'key' else (lambda: obj.pointer_button('left', False))
                down()
                obj.user32.send_error = True
                with self.assertRaisesRegex(native.Win32BackendError, 'send unavailable'):
                    self.record(obj, name + '_send_exception', up)
                self.assertEqual(obj.held_keys, {'Q': 81} if name == 'key' else {})
                self.assertEqual(obj.held_buttons, {'left'} if name == 'button' else set())

    def test_state_read_failure_after_explicit_up_preserves_obligation(self):
        obj = self.backend(stubborn=True, query_error=True)
        obj.key_state('Q', True)
        with self.assertRaisesRegex(RuntimeError, 'read unavailable'):
            self.record(obj, 'explicit_up_query_exception', lambda: obj.key_state('Q', False))
        self.assertEqual(obj.held_keys, {'Q': 81})

    def test_explicit_up_failure_quarantines_until_recovery(self):
        obj = self.backend(stubborn=True)
        obj.pending_unicode_ups = set()
        session = Win32RuntimeSession(obj)

        def dispatch(pid, ops):
            program = {'schema': SCHEMA_PROGRAM, 'program_id': pid,
                       'source': {'observation_seq': 7, 'binding_revision': 3},
                       'authority': {'lease_id': 'ordinary-explicit-up', 'expires_at_ns': 100},
                       'terminal': {'release_all_required': True},
                       'ops': ops + [{'op': 'release_all'}]}
            return session.dispatch(program, current_observation_seq=7,
                                    current_binding_revision=3, now_ns=1)

        failed = dispatch('explicit_up_failed', [
            {'op': 'key_state', 'key': 'Q', 'down': True},
            {'op': 'key_state', 'key': 'Q', 'down': False},
            {'op': 'text', 'text': 'x'},
        ])
        self.assertEqual(failed['status'], 'execution_failed')
        self.assertTrue(failed['recovery_required'])
        self.assertFalse(any(event.get('send') == 0 for event in obj.user32.events))
        emissions = obj.emissions
        events = list(obj.user32.events)

        refused = dispatch('quarantined', [])
        self.assertEqual(refused['status'], 'refused')
        self.assertEqual(refused['error'], 'INPUT_RECOVERY_REQUIRED')
        self.assertEqual(obj.emissions, emissions)
        self.assertEqual(obj.user32.events, events)

        obj.user32.stubborn = False
        recovered = session.recover_input()
        self.assertEqual(recovered['status'], 'input_recovered')
        self.assertFalse(session.recovery_required)
        self.assertEqual(obj.held_keys, {})
        self.assertEqual(obj.user32.down, set())

    def test_caller_later_neutral_read_retires_explicit_up_obligation(self):
        obj = self.backend(stubborn=True)
        first = self.record(obj, 'later_first', lambda: self.dispatch(obj, 'later_first',
                            [{'op': 'key_state', 'key': 'Q', 'down': True},
                             {'op': 'key_state', 'key': 'Q', 'down': False}]))
        first_ledger = dict(obj.held_keys)
        obj.user32.stubborn = False
        second = self.record(obj, 'later_second', lambda: self.dispatch(obj, 'later_second', []))
        self.assertEqual(first['status'], 'execution_failed')
        self.assertEqual(first['error'], 'BACKEND_EXECUTION')
        self.assertEqual(first_ledger, {'Q': 81})
        self.assertEqual(second['status'], 'completed')
        self.assertEqual(obj.held_keys, {})
        self.assertEqual(obj.user32.down, set())


if __name__ == '__main__':
    unittest.main()
