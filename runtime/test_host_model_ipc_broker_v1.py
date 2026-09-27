from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch


import base64
import hashlib
import os
from types import SimpleNamespace

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

    def _run_broker(self, request, *, instruction_bytes=b"fixed test instructions"):
        from runtime.host_model_ipc_broker_v1 import serve

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repo = base / "repo"
            repo.mkdir()
            request = dict(request)
            if request.get("instructions_b64") is not None:
                request.setdefault("instructions_sha256",
                                   hashlib.sha256(instruction_bytes).hexdigest())
            request.setdefault("request_id", "probe")
            request.setdefault("prompt", "fixed prompt")
            request.setdefault("working", "/repo")
            request.setdefault("schema", "/repo/schema.json")
            request.setdefault("image", None)
            ipc = base / "ipc"
            ipc.mkdir()
            (ipc / "probe.request.json").write_text(json.dumps(request), encoding="utf-8")
            observed = {}

            def fake_run(args, **kwargs):
                observed["args"] = args
                observed["input"] = kwargs["input"]
                config = next((arg for arg in args
                               if arg.startswith("model_instructions_file=")), None)
                if config is not None:
                    private_path = Path(json.loads(config.split("=", 1)[1]))
                    observed["instructions"] = private_path.read_bytes()
                    observed["private_path"] = private_path
                return SimpleNamespace(stdout="{}\n", stderr="", returncode=0)

            with patch.dict(os.environ, {"CODEX_EXE": "codex.exe"}), patch(
                "runtime.host_model_ipc_broker_v1.subprocess.run", side_effect=fake_run
            ) as run:
                status = serve(ipc, repo, once=True)
            receipt = json.loads((ipc / "probe.broker.json").read_text(encoding="utf-8"))
            response = (ipc / "probe.response.jsonl").read_text(encoding="utf-8")
            return status, receipt, response, observed, run.call_count

    def test_forwards_verified_instruction_bytes_via_private_temporary_copy(self):
        _, receipt, response, observed, calls = self._run_broker({
            "instructions_b64": base64.b64encode(b"fixed test instructions").decode("ascii"),
        })
        self.assertEqual(calls, 1)
        self.assertEqual(observed["instructions"], b"fixed test instructions")
        self.assertTrue(any(arg.startswith("model_instructions_file=")
                            for arg in observed["args"]))
        self.assertEqual(receipt["returncode"], 0)
        self.assertEqual(response, "{}\n")
        self.assertFalse(observed["private_path"].exists())

    def test_forwards_verified_instruction_bytes_with_private_copy(self):
        _, _, _, observed, calls = self._run_broker({
            "instructions_b64": base64.b64encode(b"fixed test instructions").decode("ascii"),
        })
        self.assertEqual(calls, 1)
        self.assertEqual(observed["instructions"], b"fixed test instructions")

    def test_forwards_quoted_instruction_content_without_cli_argument_injection(self):
        _, _, _, observed, calls = self._run_broker({
            "instructions_b64": base64.b64encode(b"fixed test instructions").decode("ascii"),
        })
        self.assertEqual(calls, 1)
        config = next(arg for arg in observed["args"]
                      if arg.startswith("model_instructions_file="))
        self.assertEqual(Path(json.loads(config.split("=", 1)[1])).name, "instructions.txt")
        self.assertEqual(observed["instructions"], b"fixed test instructions")

    def test_preserves_schema_image_and_prompt_arguments(self):
        _, _, _, observed, calls = self._run_broker({
            "instructions_b64": base64.b64encode(b"fixed test instructions").decode("ascii"),
            "image": "/repo/input.png",
        })
        self.assertEqual(calls, 1)
        args = observed["args"]
        self.assertTrue(args[args.index("--output-schema") + 1].replace("\\", "/")
                        .endswith("/repo/schema.json"))
        self.assertTrue(args[args.index("--image") + 1].replace("\\", "/")
                        .endswith("/repo/input.png"))
        self.assertEqual(observed["input"], "fixed prompt\n")

    def test_instructionless_schema_bridge_request_remains_supported(self):
        _, receipt, response, observed, calls = self._run_broker({})
        self.assertEqual(calls, 1)
        self.assertFalse(any(arg.startswith("model_instructions_file=")
                             for arg in observed["args"]))
        self.assertEqual(receipt["returncode"], 0)
        self.assertEqual(response, "{}\n")

    def test_rejects_legacy_path_instructions_without_cli_invocation(self):
        _, receipt, response, _, calls = self._run_broker({
            "instructions": "/repo/instructions.txt",
        })
        self.assertEqual(calls, 0)
        self.assertEqual(receipt["error_class"], "InvalidInstructions")
        self.assertEqual(receipt["stop_reason"], "HOST_MODEL_INSTRUCTIONS_REJECTED")
        self.assertEqual(response, "")

    def test_rejects_instruction_hash_mismatch_without_cli_invocation(self):
        _, receipt, response, _, calls = self._run_broker({
            "instructions_b64": base64.b64encode(b"fixed test instructions").decode("ascii"),
            "instructions_sha256": "0" * 64,
        })
        self.assertEqual(calls, 0)
        self.assertEqual(receipt["error_class"], "InvalidInstructions")
        self.assertEqual(receipt["stop_reason"], "HOST_MODEL_INSTRUCTIONS_REJECTED")
        self.assertEqual(response, "")

    def test_rejects_invalid_base64_without_cli_invocation(self):
        _, receipt, response, _, calls = self._run_broker({"instructions_b64": "%%%"})
        self.assertEqual(calls, 0)
        self.assertEqual(receipt["error_class"], "InvalidInstructions")
        self.assertEqual(response, "")

    def test_rejects_oversized_instruction_without_cli_invocation(self):
        payload = base64.b64encode(b"x" * (1024 * 1024 + 1)).decode("ascii")
        _, receipt, response, _, calls = self._run_broker({"instructions_b64": payload})
        self.assertEqual(calls, 0)
        self.assertEqual(receipt["error_class"], "InvalidInstructions")
        self.assertEqual(response, "")

    def test_broker_is_non_authoritative(self):
        source = Path(__file__).with_name("host_model_ipc_broker_v1.py").read_text()
        self.assertIn('"authority_granted": False', source)

    def test_broker_has_bounded_subprocess_timeout(self):
        source = Path(__file__).with_name("host_model_ipc_broker_v1.py").read_text()
        self.assertIn("HOST_MODEL_BROKER_TIMEOUT_S", source)
        self.assertIn("TimeoutExpired", source)


if __name__ == "__main__":
    unittest.main()
