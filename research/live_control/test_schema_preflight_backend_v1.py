import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schema_preflight_v1


class SchemaPreflightBackendTest(unittest.TestCase):
    def test_docker_module_is_selected_for_task_call_and_schema_preflight(self):
        module_dir = str(Path(__file__).resolve().parent)
        env = os.environ.copy()
        env["AGENT_INTERFACE_MODEL_BACKEND"] = "module"
        env["AGENT_INTERFACE_MODEL_CALL_MODULE"] = "docker_model_call_backend_v1"
        env["PYTHONPATH"] = module_dir + os.pathsep + env.get("PYTHONPATH", "")
        script = (
            "import docker_model_call_backend_v1 as docker; "
            "import integrated_efficiency_model_v1 as task; "
            "import schema_preflight_v1 as preflight; "
            "assert task.call is docker.call; "
            "assert preflight.run_preflight_call is docker.preflight_call; "
            "assert preflight.compatibility_identity is docker.preflight_identity"
        )
        result = subprocess.run([sys.executable, "-c", script], env=env,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_preflight_uses_selected_transport_for_fresh_endpoint_probe(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            schema = root / "schema.json"
            schema.write_text(json.dumps({
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
            }), encoding="utf-8")
            workspace = root / "workspace"
            workspace.mkdir()
            calls = []

            def selected_transport(prompt, working, output, instructions, selected_schema):
                calls.append((prompt, working, output, instructions, selected_schema))
                output.mkdir(parents=True)
                (output / "events.jsonl").write_text(json.dumps({
                    "type": "turn.completed",
                    "usage": {"input_tokens": 9, "output_tokens": 2},
                }) + "\n", encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

            identity = ({"transport": "test-module", "schema_sha256": "fixed"}, "key")
            with patch.object(schema_preflight_v1, "compatibility_identity",
                              return_value=identity), \
                 patch.object(schema_preflight_v1, "run_preflight_call",
                              side_effect=selected_transport), \
                 patch.object(schema_preflight_v1.subprocess, "run",
                              side_effect=AssertionError("legacy WSL transport must not run")):
                result = schema_preflight_v1.preflight(
                    schema, root / "cache", root / "result", workspace)

            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][3], schema_preflight_v1.INSTRUCTIONS)
            self.assertEqual(calls[0][1], workspace.resolve())
            self.assertEqual(calls[0][4], schema.resolve())
            self.assertEqual(result["endpoint_status"], "ENDPOINT_COMPATIBLE")
            self.assertEqual(result["usage"], {"input_tokens": 9, "output_tokens": 2})
            self.assertEqual(result["identity"], identity[0])

    def test_missing_runner_events_becomes_a_retained_preflight_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            schema = root / "schema.json"
            schema.write_text(json.dumps({
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
            }), encoding="utf-8")
            workspace = root / "workspace"
            workspace.mkdir()
            identity = ({"transport": "test-module"}, "key")
            with patch.object(schema_preflight_v1, "compatibility_identity",
                              return_value=identity), \
                 patch.object(schema_preflight_v1, "run_preflight_call",
                              return_value=SimpleNamespace(
                                  returncode=1, stdout=b"", stderr=b"runner stopped")):
                result = schema_preflight_v1.preflight(
                    schema, root / "cache", root / "result", workspace)
            self.assertEqual(result["endpoint_status"], "PREFLIGHT_FAILED")
            self.assertTrue(result["model_call_performed"])
            self.assertTrue((root / "result" / "preflight-result.json").is_file())


if __name__ == "__main__":
    unittest.main()
