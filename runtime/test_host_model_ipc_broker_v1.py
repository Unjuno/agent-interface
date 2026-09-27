from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch


class HostBrokerContractTest(unittest.TestCase):
    def _run_once(self, child_result=None, child_error=None):
        from runtime.host_model_ipc_broker_v1 import serve

        with tempfile.TemporaryDirectory() as directory:
            ipc = Path(directory)
            request_id = "req-1"
            (ipc / f"{request_id}.request.json").write_text(json.dumps({
                "request_id": request_id,
                "schema": "/repo/schema.json",
                "working": "/repo",
                "prompt": "probe",
            }), encoding="utf-8")
            with patch.dict("os.environ", {"CODEX_EXE": "fake-codex"}):
                with patch("runtime.host_model_ipc_broker_v1.subprocess.run",
                           side_effect=child_error, return_value=child_result):
                    status = serve(ipc, ipc, once=True)
            receipt = json.loads((ipc / f"{request_id}.broker.json").read_text())
            response = (ipc / f"{request_id}.response.jsonl").read_text()
            self.assertFalse(receipt["authority_granted"])
            self.assertEqual(receipt["boundary"], "host-local-codex-exe")
            return status, receipt, response

    def test_once_propagates_child_zero(self):
        status, receipt, response = self._run_once(
            child_result=subprocess.CompletedProcess([], 0, "ok\n", ""))
        self.assertEqual(status, 0)
        self.assertEqual(receipt["returncode"], 0)
        self.assertEqual(response, "ok\n")

    def test_once_propagates_exact_nonzero_child_status(self):
        status, receipt, response = self._run_once(
            child_result=subprocess.CompletedProcess([], 23, "partial\n", "child error"))
        self.assertEqual(status, 23)
        self.assertEqual(receipt["returncode"], 23)
        self.assertEqual(response, "partial\n")

    def test_once_timeout_is_nonzero_and_typed(self):
        status, receipt, response = self._run_once(
            child_error=subprocess.TimeoutExpired(["fake-codex"], 0.01))
        self.assertNotEqual(status, 0)
        self.assertIsNone(receipt["returncode"])
        self.assertEqual(receipt["stop_reason"], "HOST_BROKER_SUBPROCESS_TIMEOUT")
        self.assertEqual(response, "")

    def test_once_unavailable_executable_is_nonzero_and_typed(self):
        status, receipt, response = self._run_once(
            child_error=FileNotFoundError("fake-codex"))
        self.assertNotEqual(status, 0)
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
