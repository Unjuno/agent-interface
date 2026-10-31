import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from source_pixel_transform_v1 import to_window_content


class ChromiumConfigurationTests(unittest.TestCase):
    def test_configured_executable_is_forwarded_without_shell(self):
        from integrated_efficiency_client_v1 import RuntimeClient
        with patch.dict(os.environ, {"AGENT_INTERFACE_CHROMIUM": "/usr/bin/chromium"}):
            command = RuntimeClient("out", 7)._runtime_command()
        self.assertEqual(command[-2:], ["--chromium", "/usr/bin/chromium"])
        self.assertIn("--app", command)

    def test_unset_override_preserves_existing_default(self):
        from integrated_efficiency_client_v1 import RuntimeClient
        with patch.dict(os.environ, {}, clear=True):
            command = RuntimeClient("out", 7)._runtime_command()
        self.assertNotIn("--chromium", command)

    def test_empty_override_is_rejected(self):
        from integrated_efficiency_client_v1 import RuntimeClient
        with patch.dict(os.environ, {"AGENT_INTERFACE_CHROMIUM": ""}):
            with self.assertRaises(ValueError):
                RuntimeClient("out", 7)


class StartupCleanupTests(unittest.TestCase):
    def test_missing_ready_reports_failure_and_cleans_owned_resources(self):
        from integrated_efficiency_client_v1 import RuntimeClient
        process = MagicMock()
        process.stdout.readline.return_value = '{"socket":"/tmp/fake.sock"}\n'
        process.poll.return_value = None
        with tempfile.TemporaryDirectory() as directory:
            client = RuntimeClient(Path(directory) / "call", 7)
            with patch("integrated_efficiency_client_v1.subprocess.Popen", return_value=process), \
                 patch("integrated_efficiency_client_v1.start", return_value={}), \
                 patch("integrated_efficiency_client_v1.request_once", return_value={"reply":{"records":[]}}):
                with self.assertRaisesRegex(RuntimeError, "runtime did not emit ready"):
                    client.start()
            process.terminate.assert_called_once_with()
            process.wait.assert_called_once_with(timeout=10)
            self.assertTrue(client.errors.closed)
            self.assertFalse(Path(client.temporary.name).exists())

    def test_cleanup_failure_does_not_mask_startup_error(self):
        from integrated_efficiency_client_v1 import RuntimeClient
        process = MagicMock()
        process.stdout.readline.return_value = '{"socket":"/tmp/fake.sock"}\n'
        process.poll.return_value = None
        process.wait.side_effect = RuntimeError("wait failed")
        with tempfile.TemporaryDirectory() as directory:
            client = RuntimeClient(Path(directory) / "call", 7)
            with patch("integrated_efficiency_client_v1.subprocess.Popen", return_value=process), \
                 patch("integrated_efficiency_client_v1.start", return_value={}), \
                 patch("integrated_efficiency_client_v1.request_once", side_effect=TimeoutError("handshake timed out")):
                with self.assertRaisesRegex(TimeoutError, "handshake timed out") as caught:
                    client.start()
            self.assertTrue(any("wait failed" in note for note in caught.exception.__notes__))
            self.assertTrue(client.errors.closed)
            self.assertFalse(Path(client.temporary.name).exists())

    def test_request_failure_is_preserved_and_cleans_resources(self):
        from integrated_efficiency_client_v1 import RuntimeClient
        process = MagicMock()
        process.stdout.readline.return_value = '{"socket":"/tmp/fake.sock"}\n'
        process.poll.return_value = None
        with tempfile.TemporaryDirectory() as directory:
            client = RuntimeClient(Path(directory) / "call", 7)
            with patch("integrated_efficiency_client_v1.subprocess.Popen", return_value=process), \
                 patch("integrated_efficiency_client_v1.start", return_value={}), \
                 patch("integrated_efficiency_client_v1.request_once", side_effect=TimeoutError("handshake timed out")):
                with self.assertRaisesRegex(TimeoutError, "handshake timed out"):
                    client.start()
            process.terminate.assert_called_once_with()
            self.assertTrue(client.errors.closed)
            self.assertFalse(Path(client.temporary.name).exists())


class MintPointTransformTests(unittest.TestCase):
    def test_source_pixels_are_rebased_to_window_content_origin(self):
        source = {"sequence": 6, "pointer_binding": {"geometry": [10, 10, 1050, 780]}}
        grounding = {"field_point": [234, 402], "submit_point": [386, 402]}
        self.assertEqual(to_window_content(grounding["field_point"],
                                          source["pointer_binding"]["geometry"]),
                         [224, 392])
        self.assertEqual(to_window_content(grounding["submit_point"],
                                          source["pointer_binding"]["geometry"]),
                         [376, 392])

class MintAbsolutePointTests(unittest.TestCase):
    def test_mint_uses_observation_pixels_even_with_nonzero_window_origin(self):
        from integrated_efficiency_client_v1 import RuntimeClient
        client = RuntimeClient.__new__(RuntimeClient)
        calls = []
        def capture(_label, steps):
            calls.extend(steps)
            return {"terminal": {"status": "completed"}, "point_mints": [{}]}
        client.submit = capture
        aliases, refusal = client.mint("A", {"sequence": 9, "pointer_binding": {"geometry": [10, 10, 1050, 780]}}, {"field_point": [226, 401], "submit_point": [376, 401]}, "test")
        self.assertIsNone(refusal)
        self.assertEqual([s["point"] for s in calls], [[226, 401], [376, 401]])
        self.assertEqual([s["coordinate_frame"] for s in calls], ["window_content", "window_content"])


if __name__ == "__main__":
    unittest.main()
