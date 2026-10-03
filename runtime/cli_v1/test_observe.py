import unittest
from types import SimpleNamespace
from unittest import mock

from runtime.cli_v1.observe import observe, observe_in_session


class ObserveTests(unittest.TestCase):
    def test_initialization_exception_returns_observation_failure_without_retry(self):
        for error in (OSError('connection refused'), OverflowError('invalid display'), RuntimeError('setup')):
            with self.subTest(error=error), mock.patch(
                    'runtime.cli_v1.observe.open_session', side_effect=error) as opened:
                row = self.call()
                opened.assert_called_once()
                self.assertEqual(row['status'], 'observation_failed')
                self.assertEqual(row['failure_phase'], 'backend_initialization')
                self.assertEqual(row['error'], repr(error))
                self.assertFalse(row['input_dispatched'])
                self.assertNotIn('observation', row)

    def test_caller_owned_capture_preserves_recovery_and_connection(self):
        backend = mock.Mock()
        backend.observe_read_only.return_value = {"sha256": "source"}
        session = SimpleNamespace(backend=backend, recovery_required=True,
                                  dispatch=mock.Mock())
        with mock.patch("runtime.cli_v1.observe.open_session") as opened:
            first = observe_in_session(session, target="fixture", frame="window_client",
                                       region=[0, 0, 400, 180])
            second = observe_in_session(session, target="fixture", frame="window_client",
                                        region=[0, 0, 400, 180])
        self.assertEqual(first["status"], "returned")
        self.assertNotEqual(first["observation_id"], second["observation_id"])
        self.assertFalse(first["input_dispatched"])
        self.assertFalse(first["side_effect_authority"])
        self.assertTrue(session.recovery_required)
        self.assertEqual(backend.mock_calls, [
            mock.call.observe_read_only("fixture", "window_client", [0, 0, 400, 180]),
            mock.call.observe_read_only("fixture", "window_client", [0, 0, 400, 180])])
        opened.assert_not_called()
        session.dispatch.assert_not_called()

    def test_caller_owned_failure_and_invalid_request_never_close_or_retry(self):
        backend = mock.Mock()
        backend.observe_read_only.side_effect = OSError("capture")
        session = SimpleNamespace(backend=backend, recovery_required=True)
        row = observe_in_session(session, target="fixture", frame="window_client",
                                 region=[0, 0, 400, 180])
        self.assertEqual(row["status"], "observation_failed")
        self.assertTrue(session.recovery_required)
        self.assertEqual(backend.mock_calls, [
            mock.call.observe_read_only("fixture", "window_client", [0, 0, 400, 180])])
        backend.reset_mock()
        row = observe_in_session(session, target="fixture", frame="window_client",
                                 region=[False, 0, 400, 180])
        self.assertEqual(row["status"], "invalid_request")
        self.assertEqual(backend.mock_calls, [])
        self.assertEqual(observe_in_session(None, target="fixture", frame="window_client",
                         region=[0, 0, 400, 180])["error"], "INVALID_SESSION")

    def call(self, **options):
        return observe({"fixture": 42}, target="fixture", frame="window_client",
                       region=options.pop("region", [0, 0, 400, 180]), **options)

    def test_no_dispatch_focus_or_release_and_unique_observation_identity(self):
        backend = SimpleNamespace(observe_read_only=mock.Mock(return_value={"sha256": "source"}),
                                  close=mock.Mock(), configure_capture_artifacts=mock.Mock())
        session = SimpleNamespace(backend=backend, dispatch=mock.Mock())
        with mock.patch("runtime.cli_v1.observe.open_session", return_value=session):
            first = self.call(capture_directory="images")
            second = self.call()
        session.dispatch.assert_not_called()
        backend.configure_capture_artifacts.assert_called_once_with("images")
        backend.observe_read_only.assert_called_with("fixture", "window_client", [0, 0, 400, 180])
        self.assertEqual(backend.close.call_count, 2)
        self.assertNotEqual(first["observation_id"], second["observation_id"])
        self.assertFalse(first["input_dispatched"])
        self.assertFalse(first["side_effect_authority"])

    def test_close_failure_preserves_captured_observation(self):
        backend = SimpleNamespace(observe_read_only=lambda *_: {"artifact": "captured"},
                                  close=mock.Mock(side_effect=OSError("close")))
        with mock.patch("runtime.cli_v1.observe.open_session", return_value=SimpleNamespace(backend=backend)):
            row = self.call()
        self.assertEqual(row["status"], "observation_failed")
        self.assertEqual(row["observation"], {"artifact": "captured"})

    def test_unsupported_and_capture_failure_close_without_dispatch(self):
        for backend in (SimpleNamespace(close=mock.Mock()),
                        SimpleNamespace(close=mock.Mock(), observe_read_only=mock.Mock(side_effect=OSError("capture")))):
            session = SimpleNamespace(backend=backend, dispatch=mock.Mock())
            with mock.patch("runtime.cli_v1.observe.open_session", return_value=session):
                row = self.call()
            self.assertEqual(row["status"], "observation_failed")
            session.dispatch.assert_not_called()
            backend.close.assert_called_once()

    def test_invalid_region_never_opens_native_connection(self):
        for region in ([False, 0, 10, 10], [0, 0, 0, 10], [0, 0, 8192, 8192], [-1, 0, 10, 10]):
            with mock.patch("runtime.cli_v1.observe.open_session") as opened:
                row = self.call(region=region)
            self.assertEqual(row["status"], "invalid_request")
            opened.assert_not_called()



class Win32ReadOnlyObserveTests(unittest.TestCase):
    def backend_session(self):
        from runtime.backends.win32_v1.backend import Win32Backend
        from runtime.backends.win32_v1.session import Win32RuntimeSession
        backend = object.__new__(Win32Backend)
        backend.targets = {"fixture": 42}
        backend.user32 = SimpleNamespace(IsWindow=mock.Mock(return_value=True))
        backend.geometry = mock.Mock(return_value={"width": 16, "height": 16})
        backend.held_keys = {"SHIFT": 16}
        backend.held_buttons = {"left"}
        backend.emissions = 17
        pixels = bytearray()
        for y in range(16):
            for x in range(16):
                bgr = (0, 0, 255) if x < 8 and y < 8 else (0, 255, 0) if y < 8 else (255, 0, 0) if x < 8 else (0, 255, 255)
                pixels.extend((*bgr, 0))
        full = bytes(pixels)
        def captured(hwnd, x, y, width, height, *, print_window):
            if print_window:
                self.assertEqual((hwnd, x, y, width, height), (42, 0, 0, 16, 16))
                return full
            self.assertEqual(hwnd, 0)
            return b"".join(full[(y + yy) * 64 + x * 4:(y + yy) * 64 + (x + width) * 4] for yy in range(height))
        backend._capture_hdc = mock.Mock(side_effect=captured)
        backend.focus = mock.Mock(side_effect=AssertionError("focus forbidden"))
        backend.release_all = mock.Mock(side_effect=AssertionError("release forbidden"))
        session = Win32RuntimeSession(backend)
        # Synthetic marker checks facade preservation; it is not a recovery implementation claim.
        session.recovery_required = True
        session.dispatch = mock.Mock(side_effect=AssertionError("dispatch forbidden"))
        return backend, session, full

    def assert_untouched(self, backend, session):
        self.assertEqual(backend.held_keys, {"SHIFT": 16})
        self.assertEqual(backend.held_buttons, {"left"})
        self.assertEqual(backend.emissions, 17)
        self.assertTrue(session.recovery_required)
        backend.focus.assert_not_called()
        backend.release_all.assert_not_called()
        session.dispatch.assert_not_called()

    def test_existing_win32_capture_is_available_without_input_dispatch(self):
        import hashlib
        for frame in ("window_client", "screen_physical_px"):
            with self.subTest(frame=frame):
                backend, session, full = self.backend_session()
                with mock.patch("runtime.cli_v1.observe.open_session") as opened:
                    first = observe_in_session(session, target="fixture", frame=frame, region=[6, 6, 4, 4])
                    second = observe_in_session(session, target="fixture", frame=frame, region=[2, 2, 4, 4])
                self.assertEqual(first["status"], "returned")
                self.assertEqual(second["status"], "returned")
                self.assertNotEqual(first["observation_id"], second["observation_id"])
                expected = b"".join(full[y * 64 + 24:y * 64 + 40] for y in range(6, 10))
                self.assertEqual(first["observation"], {"bytes": 64, "sha256": hashlib.sha256(expected).hexdigest(), "width": 4, "height": 4})
                self.assertFalse(first["input_dispatched"])
                self.assertFalse(first["side_effect_authority"])
                self.assertEqual(backend._capture_hdc.call_count, 2)
                opened.assert_not_called()
                self.assert_untouched(backend, session)

    def test_win32_capture_failure_is_not_retried_or_recovered(self):
        from runtime.backends.win32_v1.backend import Win32BackendError
        backend, session, _ = self.backend_session()
        backend._capture_hdc.side_effect = Win32BackendError("injected capture failure")
        row = observe_in_session(session, target="fixture", frame="window_client", region=[0, 0, 4, 4])
        self.assertEqual(row["status"], "observation_failed")
        self.assertIn("injected capture failure", row["error"])
        backend._capture_hdc.assert_called_once()
        self.assert_untouched(backend, session)

    def test_win32_invalid_region_and_unknown_target_do_not_capture(self):
        for target, region in (("fixture", [False, 0, 4, 4]), ("unknown", [0, 0, 4, 4]), ("fixture", [15, 15, 4, 4])):
            with self.subTest(target=target, region=region):
                backend, session, _ = self.backend_session()
                row = observe_in_session(session, target=target, frame="window_client", region=region)
                self.assertIn(row["status"], ("invalid_request", "observation_failed"))
                backend._capture_hdc.assert_not_called()
                self.assert_untouched(backend, session)

    def test_win32_artifact_request_still_refuses_before_capture(self):
        backend, session, _ = self.backend_session()
        row = observe_in_session(session, target="fixture", frame="window_client", region=[0, 0, 4, 4], capture_directory="unused")
        self.assertEqual(row["status"], "observation_failed")
        self.assertIn("CAPTURE_ARTIFACTS_UNSUPPORTED", row["error"])
        backend._capture_hdc.assert_not_called()
        self.assert_untouched(backend, session)


if __name__ == '__main__':
    unittest.main()
