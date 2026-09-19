import unittest
from types import SimpleNamespace
from unittest import mock

from runtime.cli_v1.observe import observe


class ObserveTests(unittest.TestCase):
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
