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
                self.assertEqual(reply['admission'], 'accepted')
                release = reply['execution']['releases'][-1]
                self.assertIs(release['verified'], not stubborn)
                self.assertEqual(reply['status'], 'release_unverified' if stubborn else 'completed')
                self.assertEqual(obj.user32.down, {vk} if stubborn else set())
                self.assertEqual(obj.held_keys, {key: vk} if stubborn and key else {})
                self.assertEqual(obj.held_buttons, {button} if stubborn and button else set())
                if stubborn:
                    self.assertEqual(release['keys_down'], [key] if key else [])
                    self.assertEqual(release['buttons_down'], [button] if button else [])

    def test_key_pair_terminal_rejects_reported_down_input(self):
        ops = [{'op': 'key_state', 'key': 'Q', 'down': True},
               {'op': 'key_state', 'key': 'Q', 'down': False}]
        self.family('key_pair', ops, 81, key='Q')
        obj = self.backend()
        reply = self.dispatch(obj, 'key_pair_measurement', ops)
        transitions = reply['execution']['input_transitions']
        ordinary = [row for row in transitions if not row['cleanup']]
        self.assertEqual([(row['operation'], row['key']) for row in ordinary],
                         [('down', 'Q'), ('up', 'Q')])
        self.assertEqual([row['program_id'] for row in ordinary],
                         ['key_pair_measurement', 'key_pair_measurement'])
        self.assertEqual([row['operation_index'] for row in ordinary], [0, 1])
        self.assertEqual([row['admitted_ns'] for row in ordinary], [123456, 123456])
        self.assertEqual(ordinary[0]['hold_id'], ordinary[1]['hold_id'])
        self.assertEqual(ordinary[0]['os_key_state_classification'],
                         'OS_KEY_STATE_DOWN_CONFIRMED')
        self.assertEqual(ordinary[1]['os_key_state_classification'],
                         'OS_KEY_STATE_UP_CONFIRMED')
        self.assertEqual(ordinary[0]['os_state_change_window_ns'], [123456, 123456])
        self.assertEqual(ordinary[1]['os_state_change_window_ns'], [123456, 123456])
        self.assertLessEqual(ordinary[0]['requested_ns'],
                             ordinary[0]['sendinput_acknowledged_ns'])
        self.assertLessEqual(ordinary[1]['requested_ns'],
                             ordinary[1]['sendinput_acknowledged_ns'])
        self.assertFalse(ordinary[1]['physical_keyboard_state_proven'])
        self.assertFalse(ordinary[1]['application_delivery_proven'])

    def test_stubborn_key_preserves_unconfirmed_per_key_up_receipt(self):
        obj = self.backend(stubborn=True)
        reply = self.dispatch(obj, 'stubborn_key', [
            {'op': 'key_state', 'key': 'Q', 'down': True},
            {'op': 'key_state', 'key': 'Q', 'down': False},
        ])
        self.assertEqual(reply['status'], 'release_unverified')
        ordinary = [row for row in reply['execution']['input_transitions']
                    if not row['cleanup']]
        self.assertEqual(len(ordinary), 2)
        self.assertEqual(ordinary[1]['hold_id'], ordinary[0]['hold_id'])
        self.assertEqual(ordinary[1]['os_key_state_classification'],
                         'OS_KEY_STATE_UP_UNCONFIRMED')
        self.assertTrue(ordinary[1]['state_after']['down'])

    def test_down_after_unconfirmed_up_keeps_same_owned_hold(self):
        obj = self.backend(stubborn=True)
        reply = self.dispatch(obj, 'retry_same_key_after_unconfirmed_up', [
            {'op': 'key_state', 'key': 'Q', 'down': True},
            {'op': 'key_state', 'key': 'Q', 'down': False},
            {'op': 'key_state', 'key': 'Q', 'down': True},
        ])
        self.assertEqual(reply['status'], 'release_unverified')
        transitions = reply['execution']['input_transitions']
        ordinary = [row for row in transitions if not row['cleanup']]
        self.assertEqual([row['os_key_state_classification'] for row in ordinary],
                         ['OS_KEY_STATE_DOWN_CONFIRMED',
                          'OS_KEY_STATE_UP_UNCONFIRMED',
                          'OS_KEY_STATE_ALREADY_DOWN'])
        self.assertEqual(len({row['hold_id'] for row in ordinary}), 1)
        self.assertEqual(transitions[-1]['hold_id'], ordinary[0]['hold_id'])

    def test_key_state_query_failure_is_recorded_without_blocking_send(self):
        obj = self.backend(query_error=True)
        obj.key_state('Q', True)
        self.assertEqual(obj.user32.down, {81})
        self.assertEqual(obj.last_input_transitions[0]['os_key_state_classification'],
                         'OS_KEY_STATE_UNAVAILABLE')

    def test_failed_execution_preserves_transitions_when_cleanup_also_fails(self):
        obj = self.backend()
        obj.pending_unicode_ups = {ord('x')}
        real_query = obj.user32.GetAsyncKeyState
        query_count = 0

        def fail_aggregate_query(vk):
            nonlocal query_count
            query_count += 1
            # The key DOWN's pre/post samples and cleanup's pre-sample succeed.
            # Fail the strict aggregate sample after cleanup UP was recorded.
            if query_count == 4:
                raise RuntimeError('aggregate state unavailable')
            return real_query(vk)

        obj.user32.GetAsyncKeyState = fail_aggregate_query
        program = {'schema': SCHEMA_PROGRAM, 'program_id': 'cleanup_failure',
                   'source': {'observation_seq': 7, 'binding_revision': 3},
                   'authority': {'lease_id': 'ordinary-explicit-up', 'expires_at_ns': 100},
                   'terminal': {'release_all_required': True},
                   'ops': [{'op': 'key_state', 'key': 'Q', 'down': True},
                           {'op': 'text', 'text': 'x'},
                           {'op': 'release_all'}]}

        reply = Win32RuntimeSession(obj).dispatch(
            program, current_observation_seq=7, current_binding_revision=3, now_ns=1)

        self.assertEqual(reply['status'], 'execution_failed', reply)
        self.assertEqual(reply['release']['verified'], False)
        self.assertEqual(reply['release']['error'], 'RuntimeError')
        self.assertEqual(reply['release']['detail'], 'aggregate state unavailable')
        transitions = reply['input_transitions']
        self.assertEqual([(row['operation'], row['cleanup']) for row in transitions],
                         [('down', False), ('up', True)])
        self.assertEqual(transitions[0]['hold_id'], transitions[1]['hold_id'])
        self.assertEqual(transitions[1]['os_key_state_classification'],
                         'OS_KEY_STATE_POST_SAMPLE_PENDING')
        self.assertFalse(transitions[1]['physical_keyboard_state_proven'])
        self.assertFalse(transitions[1]['application_delivery_proven'])

    def test_button_pair_terminal_rejects_reported_down_input(self):
        self.family('button_pair', [{'op': 'pointer_button', 'button': 'left', 'down': True},
                                    {'op': 'pointer_button', 'button': 'left', 'down': False}], 1, button='left')

    def test_chord_terminal_rejects_reported_down_input(self):
        self.family('chord', [{'op': 'key_chord', 'keys': ['Q']}], 81, key='Q')

    def test_untracked_up_does_not_claim_unowned_inputs(self):
        obj = self.backend(stubborn=True)
        obj.user32.down = {81, 1}
        obj.key_state('Q', False)
        obj.pointer_button('left', False)
        release = self.record(obj, 'untracked_control', obj.release_all)
        self.assertIs(release['verified'], True)
        self.assertEqual(obj.held_keys, {})
        self.assertEqual(obj.held_buttons, set())
        self.assertEqual(obj.user32.down, {81, 1})
        self.assertFalse(any('query' in event for event in obj.user32.events))

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
        obj.key_state('Q', False)
        with self.assertRaisesRegex(RuntimeError, 'read unavailable'):
            self.record(obj, 'explicit_up_query_exception', obj.release_all)
        self.assertEqual(obj.held_keys, {'Q': 81})

    def test_caller_later_neutral_read_retires_explicit_up_obligation(self):
        obj = self.backend(stubborn=True)
        first = self.record(obj, 'later_first', lambda: self.dispatch(obj, 'later_first',
                            [{'op': 'key_state', 'key': 'Q', 'down': True},
                             {'op': 'key_state', 'key': 'Q', 'down': False}]))
        first_ledger = dict(obj.held_keys)
        obj.user32.stubborn = False
        second = self.record(obj, 'later_second', lambda: self.dispatch(obj, 'later_second', []))
        self.assertEqual(first['status'], 'release_unverified')
        self.assertEqual(first_ledger, {'Q': 81})
        self.assertEqual(second['status'], 'completed')
        self.assertEqual(obj.held_keys, {})
        self.assertEqual(obj.user32.down, set())


if __name__ == '__main__':
    unittest.main()
