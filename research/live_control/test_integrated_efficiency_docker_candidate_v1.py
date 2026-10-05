"""Verify Docker successor wiring without invoking Docker or a model."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


LIVE = Path(__file__).parent
sys.path.insert(0, str(LIVE))
SPEC = importlib.util.spec_from_file_location(
    "docker_candidate_runner_under_test",
    LIVE / "run_integrated_efficiency_docker_candidate_v1.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class DockerCandidateWiringTests(unittest.TestCase):
    def _success(self):
        return {"status": "ENDPOINT_COMPATIBLE", "fresh": True,
                "call_id": "fresh-call", "requested_model": "gpt-5.6-luna",
                "requested_effort": "low", "model_visible_images": 0,
                "retry_performed": False,
                "usage": {"input_tokens": 10, "cached_input_tokens": 2,
                          "cache_write_input_tokens": 0, "output_tokens": 3,
                          "reasoning_output_tokens": 1}}

    def test_preflight_adapter_maps_contract_and_requires_complete_usage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            observed = []

            def fake_preflight(call_root, schema, instructions, workspace):
                observed.append((call_root, schema, instructions, workspace))
                return self._success()

            with patch.object(RUNNER.docker_backend, "preflight_schema",
                              side_effect=fake_preflight):
                result = RUNNER._preflight_for(root)("ephemeral", "compiled")
            call_root, schema, instructions, workspace = observed[0]
            self.assertEqual(call_root.resolve(),
                             (root / "preflight" / "ephemeral" / "docker-backend").resolve())
            self.assertEqual(schema, RUNNER.CONTRACTS["compiled"][0])
            self.assertEqual(instructions, RUNNER.CONTRACTS["compiled"][1])
            self.assertTrue(workspace.is_dir())
            self.assertEqual(result, {
                "call_id": "fresh-call", "stage": "schema_preflight",
                "requested_model": "gpt-5.6-luna", "requested_effort": "low",
                "usage": self._success()["usage"], "model_visible_images": 0})

    def test_preflight_refuses_incomplete_usage_before_arm_can_start(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            invalid = self._success()
            del invalid["usage"]["reasoning_output_tokens"]
            with patch.object(RUNNER.docker_backend, "preflight_schema",
                              return_value=invalid):
                with self.assertRaisesRegex(RuntimeError,
                                            "STOP_DOCKER_PREFLIGHT_INCOMPLETE_PROVIDER_USAGE"):
                    RUNNER._preflight_for(root)("plain", "plain")
            self.assertTrue((root / "workspaces" / "plain").is_dir())

    def test_run_binds_docker_backends_and_explicit_output_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "new-allocation"
            root.mkdir()
            image_ref = "pinned-runtime@sha256:" + "c" * 64
            (root / "preregistration.json").write_text(json.dumps({
                "docker_runtime": {"image_ref": image_ref,
                                   "platform": "linux/arm64"},
                "sources": {name: "frozen-digest" for name in
                            RUNNER.REQUIRED_PREREG_SOURCES}}), encoding="utf-8")
            with patch.dict("os.environ", {
                    "AGENT_INTERFACE_DOCKER_IMAGE": image_ref,
                    "AGENT_INTERFACE_DOCKER_PLATFORM": "linux/arm64"}, clear=False), \
                 patch.object(RUNNER.integrated_runner, "main",
                              return_value={"disposition": "HOLD"}) as main:
                result = RUNNER.run(root)
            kwargs = main.call_args.kwargs
            self.assertIs(kwargs["model_call"], RUNNER.docker_backend.call)
            self.assertIsNotNone(kwargs["schema_preflight"])
            self.assertEqual(kwargs["output_root"], root.resolve())
            self.assertEqual(result, {"disposition": "HOLD"})

    def test_run_refuses_runtime_identity_drift_before_runner_or_preflight(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image_ref = "pinned-runtime@sha256:" + "c" * 64
            (root / "preregistration.json").write_text(json.dumps({
                "docker_runtime": {"image_ref": image_ref,
                                   "platform": "linux/arm64"},
                "sources": {name: "frozen-digest" for name in
                            RUNNER.REQUIRED_PREREG_SOURCES}}), encoding="utf-8")
            with patch.dict("os.environ", {
                    "AGENT_INTERFACE_DOCKER_IMAGE": "different@sha256:" + "d" * 64,
                    "AGENT_INTERFACE_DOCKER_PLATFORM": "linux/arm64"}, clear=False), \
                 patch.object(RUNNER.integrated_runner, "main") as main:
                with self.assertRaisesRegex(RuntimeError,
                    "STOP_DOCKER_RUNTIME_IDENTITY_DIFFERS_FROM_PREREGISTRATION"):
                    RUNNER.run(root)
                main.assert_not_called()


if __name__ == "__main__":
    unittest.main()
