from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch


class HostBrokerContractTest(unittest.TestCase):
    def run_once_with_child(self, child_result=None, child_error=None):
        from runtime.host_model_ipc_broker_v1 import serve

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            ipc = root / "ipc"
            ipc.mkdir()
            request = {
                "request_id": "one-shot-01",
                "prompt": "Return the fixed test response.",
                "schema": "/repo/schema.json",
                "working": "/repo",
            }
            (ipc / "one-shot-01.request.json").write_text(json.dumps(request))
            with patch("runtime.host_model_ipc_broker_v1.subprocess.run") as run:
                if child_error is not None:
                    run.side_effect = child_error
                else:
                    run.return_value = child_result
                process_returncode = serve(ipc, root, once=True)
            receipt = json.loads((ipc / "one-shot-01.broker.json").read_text())
            response = (ipc / "one-shot-01.response.jsonl").read_text()
        return process_returncode, receipt, response

    def test_once_preserves_zero_child_exit(self):
        child = subprocess.CompletedProcess(["fake-codex"], 0, "{}\\n", "")
        process_returncode, receipt, response = self.run_once_with_child(child_result=child)
        self.assertEqual(process_returncode, 0)
        self.assertEqual(receipt["returncode"], 0)
        self.assertEqual(response, "{}\\n")

    def test_once_propagates_nonzero_child_exit(self):
        child = subprocess.CompletedProcess(["fake-codex"], 23, "", "fixture failure")
        process_returncode, receipt, response = self.run_once_with_child(child_result=child)
        self.assertEqual(process_returncode, 23)
        self.assertEqual(receipt["returncode"], 23)
        self.assertEqual(response, "")

    def test_once_timeout_remains_nonzero_and_typed(self):
        timeout = subprocess.TimeoutExpired(["fake-codex"], 0.01)
        process_returncode, receipt, response = self.run_once_with_child(child_error=timeout)
        self.assertNotEqual(process_returncode, 0)
        self.assertIsNone(receipt["returncode"])
        self.assertEqual(receipt["stop_reason"], "HOST_BROKER_SUBPROCESS_TIMEOUT")
        self.assertEqual(response, "")

    def test_once_unavailable_executable_remains_nonzero_and_typed(self):
        process_returncode, receipt, response = self.run_once_with_child(
            child_error=FileNotFoundError("fake Codex executable unavailable")
        )
        self.assertNotEqual(process_returncode, 0)
        self.assertIsNone(receipt["returncode"])
        self.assertEqual(receipt["stop_reason"], "HOST_BROKER_EXECUTABLE_UNAVAILABLE")
        self.assertEqual(response, "")

    def test_maps_container_repo_paths(self):
        from runtime.host_model_ipc_broker_v1 import host_path
        self.assertEqual(Path(host_path("/repo/runtime/a.png", Path("C:/repo"))),
                         Path("C:/repo/runtime/a.png"))
        self.assertIsNone(host_path(None, Path("C:/repo")))

    def test_maps_container_workspace_paths(self):
        from runtime.host_model_ipc_broker_v1 import host_path
        self.assertEqual(Path(host_path("/workspace/runtime/a.png", Path("C:/repo"))),
                         Path("C:/repo/runtime/a.png"))

    def test_broker_is_non_authoritative(self):
        source = Path(__file__).with_name("host_model_ipc_broker_v1.py").read_text()
        self.assertIn('"authority_granted": False', source)

    def test_broker_has_bounded_subprocess_timeout(self):
        source = Path(__file__).with_name("host_model_ipc_broker_v1.py").read_text()
        self.assertIn("HOST_MODEL_BROKER_TIMEOUT_S", source)
        self.assertIn("TimeoutExpired", source)


if __name__ == "__main__":
    unittest.main()
