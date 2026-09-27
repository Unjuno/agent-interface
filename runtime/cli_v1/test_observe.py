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


if __name__ == '__main__':
    unittest.main()
