"""Failure after an effect must not erase the prefix or masquerade as success."""
import unittest
from unittest import mock

from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
from runtime.cli_v1.golden_v3 import dispatch_golden_v3
from runtime.core_v1.contract import OFFICE_FLOOR, capability_manifest
from runtime.core_v1.test_contract import program


class PartialExecutionTests(unittest.TestCase):
    def test_unsupported_verify_refuses_entire_program_before_input(self):
        from runtime.backends.x11_v1.backend import X11BackendError
        backend = object.__new__(X11Backend)
        backend.d = mock.Mock()
        backend.d.pending_events.return_value = 0
        backend._keyboard_mapping_snapshot = mock.Mock(return_value=('stable-test-map',))
        backend._text_plan = mock.Mock(return_value=[['a']])
        backend.text = mock.Mock()
        backend.release_all = mock.Mock()
        backend.emissions = 0
        # A trailing verification must not allow the preceding edit to run.
        with self.assertRaisesRegex(X11BackendError, 'verify.*not implemented'):
            backend.execute({'ops': [
                {'op': 'text', 'text': 'a'},
                {'op': 'verify', 'predicate': 'saved'},
                {'op': 'release_all'}]})
        backend.text.assert_not_called()
        backend.release_all.assert_not_called()
        self.assertEqual(backend.emissions, 0)

    def test_explicit_recovery_requires_verified_empty_readback(self):
        backend = mock.Mock()
        session = X11RuntimeSession(backend)
        self.assertEqual(session.recover_input()['error'], 'INPUT_RECOVERY_NOT_REQUIRED')
        backend.release_all.assert_not_called()
        session.recovery_required = True
        backend.release_all.side_effect = [OSError('offline'),
            {'verified': True, 'keys_down': ['w'], 'buttons_down': []},
            {'verified': True, 'keys_down': [], 'buttons_down': []}]
        self.assertEqual(session.recover_input()['status'], 'recovery_failed')
        self.assertTrue(session.recovery_required)
        self.assertEqual(session.recover_input()['status'], 'recovery_failed')
        self.assertTrue(session.recovery_required)
        self.assertEqual(session.recover_input()['status'], 'input_recovered')
        self.assertFalse(session.recovery_required)
        backend.execute.assert_not_called()
        self.assertEqual(backend.release_all.call_count, 3)

    def test_uncertain_press_is_released_after_send_or_sync_failure(self):
        from Xlib import X
        from runtime.backends.x11_v1.backend import X11ExecutionError
        for pointer in (False, True):
            for boundary in ('send', 'sync'):
                with self.subTest(pointer=pointer, boundary=boundary):
                    backend = object.__new__(X11Backend)
                    backend.d = mock.Mock()
                    backend.root = mock.Mock()
                    backend.held_keycodes = {}
                    backend.held_buttons = set()
                    backend.emissions = 0
                    backend.preflight = mock.Mock()
                    backend._refresh_keyboard_mapping = mock.Mock(return_value=False)
                    backend._keycode = lambda key: 38
                    backend.text = mock.Mock()
                    physical = {'down': False}
                    press = X.ButtonPress if pointer else X.KeyPress
                    release = X.ButtonRelease if pointer else X.KeyRelease

                    def emit(display, event, code):
                        if event == press:
                            physical['down'] = True
                            if boundary == 'send':
                                raise OSError('request sent before error')
                        elif event == release:
                            physical['down'] = False

                    def keymap():
                        result = bytearray(32)
                        if not pointer and physical['down']:
                            result[38 // 8] |= 1 << (38 % 8)
                        return result

                    backend.d.query_keymap.side_effect = keymap
                    backend.root.query_pointer.side_effect = lambda: type('Pointer', (), {
                        'mask': X.Button1Mask if pointer and physical['down'] else 0})()
                    if boundary == 'sync':
                        backend.d.sync.side_effect = [OSError('lost sync reply'), None]
                    op = ({'op': 'pointer_button', 'button': 'left', 'down': True} if pointer
                          else {'op': 'key_state', 'key': 'w', 'down': True})
                    with mock.patch('runtime.backends.x11_v1.backend.xtest.fake_input', side_effect=emit):
                        with self.assertRaises(X11ExecutionError) as caught:
                            backend.execute({'ops': [op, {'op': 'text', 'text': 'must-not-run'}]})
                    self.assertFalse(physical['down'])
                    self.assertTrue(caught.exception.execution['releases'][-1]['verified'])
                    self.assertEqual(caught.exception.execution['completed_ops'], [])
                    backend.text.assert_not_called()
                    self.assertEqual(backend.held_keycodes, {})
                    self.assertEqual(backend.held_buttons, set())

    def test_release_readback_error_keeps_obligations_for_explicit_recovery(self):
        backend = object.__new__(X11Backend)
        backend.d = mock.Mock()
        backend.emissions = 0
        backend.held_keycodes = {'w': 38}
        backend.held_buttons = {'left'}
        backend._physical_keys_down = mock.Mock(side_effect=[OSError('readback lost'), []])
        backend._physical_buttons_down = mock.Mock(return_value=[])
        with mock.patch('runtime.backends.x11_v1.backend.xtest.fake_input') as emit:
            with self.assertRaises(OSError):
                backend.release_all()
            self.assertEqual(backend.held_keycodes, {'w': 38})
            self.assertEqual(backend.held_buttons, {'left'})
            result = backend.release_all()
        self.assertEqual(emit.call_count, 4)
        self.assertTrue(result['verified'])
        self.assertEqual(backend.held_keycodes, {})
        self.assertEqual(backend.held_buttons, set())

    def test_release_down_readback_keeps_only_outstanding_inputs(self):
        backend = object.__new__(X11Backend)
        backend.d = mock.Mock()
        backend.emissions = 0
        backend.held_keycodes = {'w': 38, 's': 39}
        backend.held_buttons = {'left', 'right'}
        backend._physical_keys_down = mock.Mock(side_effect=[['w'], []])
        backend._physical_buttons_down = mock.Mock(side_effect=[['left'], []])
        with mock.patch('runtime.backends.x11_v1.backend.xtest.fake_input') as emit:
            self.assertFalse(backend.release_all()['verified'])
            self.assertEqual(backend.held_keycodes, {'w': 38})
            self.assertEqual(backend.held_buttons, {'left'})
            self.assertTrue(backend.release_all()['verified'])
        self.assertEqual(emit.call_count, 6)

    def test_target_disappearing_after_session_preflight_returns_failure(self):
        from runtime.backends.x11_v1.backend import X11BackendError
        from runtime.core_v1.contract import WINDOW_ACTIVATE
        backend = object.__new__(X11Backend)
        backend.emissions = 0
        backend.monotonic_ns = lambda: 9000
        backend.manifest = lambda: capability_manifest(
            'inert', 'linux', 'x11', OFFICE_FLOOR | {WINDOW_ACTIVATE})
        backend.preflight = mock.Mock(side_effect=[None, X11BackendError('client withdrawn')])
        backend.activate = mock.Mock()
        backend.release_all = mock.Mock(return_value={
            'verified': True, 'keys_down': [], 'buttons_down': []})
        row = program()
        row['ops'] = [{'op': 'activate', 'target': 'app', 'timeout_ms': 25},
                      {'op': 'release_all'}]
        session = X11RuntimeSession(backend)
        result = session.dispatch(row, current_observation_seq=7, current_binding_revision=3)
        self.assertEqual(result['status'], 'refused')
        self.assertEqual(result['error'], 'BACKEND_CONSTRAINT')
        self.assertFalse(session.recovery_required)
        self.assertEqual(result['backend_emissions'], 0)
        self.assertIs(result['program_execution_started'], False)
        self.assertIs(result['cleanup_attempted'], True)
        self.assertEqual(result['program_emissions'], 0)
        self.assertTrue(result['release']['verified'])
        backend.activate.assert_not_called()
        backend.release_all.assert_called_once()

    def test_preflight_refusal_distinguishes_prior_and_cleanup_emissions(self):
        from runtime.backends.x11_v1.backend import X11BackendError
        from runtime.cli_v1.review import outcome_summary
        backend = mock.Mock()
        backend.emissions = 16
        backend.monotonic_ns.return_value = 9000
        backend.manifest.return_value = capability_manifest('inert', 'linux', 'x11', OFFICE_FLOOR)
        backend.preflight.side_effect = X11BackendError('observe requires focused target')
        def cleanup():
            backend.emissions += 1
            return {'verified': True, 'keys_down': [], 'buttons_down': []}
        backend.release_all.side_effect = cleanup
        row = X11RuntimeSession(backend).dispatch(program(), current_observation_seq=7,
                                                  current_binding_revision=3)
        backend.execute.assert_not_called()
        backend.release_all.assert_called_once()
        self.assertEqual(row['backend_emissions'], 17)
        self.assertEqual(row['program_emissions'], 0)
        self.assertIs(row['program_execution_started'], False)
        self.assertIs(row['cleanup_attempted'], True)
        summary = outcome_summary({'schema':'agent-interface/runtime-dispatch-result-v1',
                                   'status':'returned', 'result':row})
        self.assertIs(summary['program_execution_started'], False)
        self.assertIs(summary['cleanup_attempted'], True)
        self.assertTrue(summary['input_release_verified'])
        self.assertEqual(summary['program_emissions'], 0)
        self.assertNotIn('input_dispatched', summary)
        old = dict(row)
        for key in ('program_execution_started', 'cleanup_attempted', 'program_emissions'):
            old.pop(key)
        historical = outcome_summary({'schema':'agent-interface/runtime-dispatch-result-v1',
                                      'status':'returned', 'result':old})
        self.assertNotIn('program_execution_started', historical)
        malformed = outcome_summary({'schema':'agent-interface/runtime-dispatch-result-v1',
            'status':'returned', 'result':{**row, 'program_execution_started':'false',
                                          'cleanup_attempted':0, 'program_emissions':False}})
        self.assertIsNone(malformed['program_execution_started'])
        self.assertIsNone(malformed['cleanup_attempted'])
        self.assertIsNone(malformed['program_emissions'])

    def test_activation_timeout_retains_request_and_stops_following_edit(self):
        from runtime.backends.x11_v1.backend import X11BackendError, X11ExecutionError
        backend = object.__new__(X11Backend)
        backend.emissions = 0
        backend.preflight = mock.Mock()
        backend._refresh_keyboard_mapping = mock.Mock(return_value=False)
        backend.text = mock.Mock()
        backend.release_all = mock.Mock(return_value={
            'verified': True, 'keys_down': [], 'buttons_down': []})

        def activate(target, timeout, receipt):
            receipt.update(target=target, requested_ms=timeout,
                           request_attempted=True, status='timeout')
            raise X11BackendError('activation not confirmed; request may take effect later')

        backend.activate = mock.Mock(side_effect=activate)
        with self.assertRaises(X11ExecutionError) as caught:
            backend.execute({'ops': [
                {'op': 'activate', 'target': 'app', 'timeout_ms': 25},
                {'op': 'text', 'text': 'must-not-run'}, {'op': 'release_all'}]})
        evidence = caught.exception.execution
        self.assertEqual(evidence['completed_ops'], [])
        self.assertEqual(evidence['failed_op'], 0)
        self.assertEqual(evidence['activations'][0]['status'], 'timeout')
        self.assertTrue(evidence['activations'][0]['request_attempted'])
        self.assertTrue(evidence['releases'][0]['verified'])
        backend.activate.assert_called_once()
        backend.text.assert_not_called()
        backend.release_all.assert_called_once()

    def test_wait_receipt_survives_later_failure_without_claiming_an_update(self):
        from runtime.backends.x11_v1.backend import X11ExecutionError
        backend = object.__new__(X11Backend)
        backend.emissions = 0
        backend.preflight = mock.Mock()
        backend._refresh_keyboard_mapping = mock.Mock(return_value=False)
        backend.text = mock.Mock(side_effect=OSError('input failure'))
        backend.release_all = mock.Mock(return_value={'verified': True})
        for interrupted in (False, True):
            with mock.patch('runtime.backends.x11_v1.backend.time.sleep',
                            side_effect=OSError('wait interrupted') if interrupted else None) as sleep:
                with self.assertRaises(X11ExecutionError) as caught:
                    backend.execute({'ops': [{'op': 'wait_update', 'timeout_ms': 25},
                                             {'op': 'text', 'text': 'fault'}]})
            evidence = caught.exception.execution
            sleep.assert_called_once_with(.025)
            self.assertEqual(evidence['completed_ops'], [] if interrupted else [0])
            self.assertEqual(evidence['failed_op'], 0 if interrupted else 1)
            self.assertEqual(evidence['observations'], [])
            self.assertEqual(evidence['program_emissions'], 0)
            self.assertEqual(len(evidence['waits']), 1)
            wait = evidence['waits'][0]
            self.assertEqual((wait['operation_index'], wait['requested_ms'], wait['kind']),
                             (0, 25, 'fixed_delay'))
            self.assertIs(wait['completed'], not interrupted)
            self.assertIsNone(wait['update_observed'])
            self.assertLessEqual(evidence['started_ns'], wait['started_ns'])
            self.assertLessEqual(wait['started_ns'], wait['ended_ns'])
            self.assertLessEqual(wait['ended_ns'], evidence['ended_ns'])

    def test_unverified_release_blocks_later_dispatch_before_backend_access(self):
        for releases in (None, [None], [], [{"verified": True}], [{"verified": False}], [{"verified": "true"}],
                         [{"verified": True, "keys_down": [], "buttons_down": ["left"]}]):
            backend = mock.Mock()
            backend.emissions = 4
            backend.monotonic_ns.return_value = 9000
            backend.manifest.return_value = capability_manifest("inert", "linux", "x11", OFFICE_FLOOR)
            backend.execute.return_value = {"releases": releases}
            session = X11RuntimeSession(backend)
            first = session.dispatch(program(), current_observation_seq=7, current_binding_revision=3)
            self.assertEqual(first["status"], "release_unverified")
            self.assertTrue(first["recovery_required"])
            backend.reset_mock()
            second = session.dispatch(program(), current_observation_seq=8, current_binding_revision=4)
            self.assertEqual(second["error"], "INPUT_RECOVERY_REQUIRED")
            self.assertFalse(second["input_dispatched"])
            self.assertEqual(backend.mock_calls, [])

    def test_unexpected_execution_exception_leaves_session_blocked(self):
        backend = mock.Mock()
        backend.emissions = 1
        backend.monotonic_ns.return_value = 9000
        backend.manifest.return_value = capability_manifest("inert", "linux", "x11", OFFICE_FLOOR)
        backend.execute.side_effect = OSError("lost execution receipt")
        session = X11RuntimeSession(backend)
        with self.assertRaises(OSError):
            session.dispatch(program(), current_observation_seq=7, current_binding_revision=3)
        self.assertTrue(session.recovery_required)
        self.assertEqual(session.dispatch(program(), current_observation_seq=7,
                         current_binding_revision=3)["error"], "INPUT_RECOVERY_REQUIRED")

    def test_partial_operation_and_observation_survive_failure_and_close(self):
        for release_fails, close_fails in ((False, False), (True, False), (False, True)):
            with self.subTest(release=release_fails, close=close_fails):
                backend = object.__new__(X11Backend)
                backend.emissions = 0
                backend.preflight = mock.Mock()
                backend._refresh_keyboard_mapping = mock.Mock(return_value=False)
                backend.focus = mock.Mock()
                backend.capture = mock.Mock(return_value={"sha256": "earlier-observation"})
                backend.monotonic_ns = lambda: 9000
                backend.manifest = lambda: capability_manifest("inert", "linux", "x11", OFFICE_FLOOR)
                calls = []

                def text(value):
                    calls.append(value)
                    backend.emissions += 1
                    if value == "fault":
                        raise OSError("after partial emission")

                backend.text = text
                backend.close = mock.Mock(side_effect=OSError("close failed") if close_fails else None)
                backend.release_all = mock.Mock(return_value={"verified": True, "keys_down": [], "buttons_down": []},
                                               side_effect=OSError("release failed") if release_fails else None)
                p = program()
                p["ops"] = [
                    {"op": "focus", "target": "window-1"},
                    {"op": "observe", "frame": "window_client", "x": 0, "y": 0, "w": 10, "h": 10},
                    {"op": "text", "text": "done"}, {"op": "text", "text": "fault"},
                    {"op": "text", "text": "mustnotrun"}, {"op": "release_all"},
                ]
                with mock.patch("runtime.cli_v1.api.open_session", return_value=X11RuntimeSession(backend)):
                    row = dispatch_golden_v3(p, {"window-1": 1}, current_observation_seq=7,
                                             current_binding_revision=3)
                self.assertEqual(calls, ["done", "fault"])
                self.assertFalse(row["program_completed"])
                self.assertEqual(row["status"], "cleanup_failed" if close_fails else "partial")
                self.assertEqual(row["raw_dispatch"]["result"]["recovery_required"], release_fails)
                evidence = row["raw_dispatch"]["result"]["execution"]
                self.assertEqual(evidence["completed_ops"], [0, 1, 2])
                self.assertEqual(evidence["failed_op"], 3)
                self.assertEqual(evidence["program_emissions"], 2)
                self.assertIn("unknown", evidence["failed_op_effect"])
                self.assertIn("partial emission", evidence["error"])
                self.assertEqual(evidence["observations"], [{"sha256": "earlier-observation", "operation_index": 1}])
                self.assertLess(evidence["observations"][0]["operation_index"], evidence["completed_ops"][-1])
                self.assertLess(evidence["observations"][0]["operation_index"], evidence["failed_op"])
                self.assertEqual(backend.capture.return_value, {"sha256": "earlier-observation"})
                self.assertEqual(evidence["releases"][-1]["verified"], not release_fails)
                if release_fails:
                    self.assertIn("release failed", evidence["releases"][-1]["error"])
                backend.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
