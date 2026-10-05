import os
import json
import hashlib
import subprocess
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import docker_model_call_backend_v1 as backend
from docker_model_call_backend_v1 import build_command, call

class DockerBackendTest(unittest.TestCase):
    def setUp(self):
        configured = patch.dict(os.environ, {
            "AGENT_INTERFACE_DOCKER_IMAGE": "test@sha256:" + "e" * 64,
            "AGENT_INTERFACE_DOCKER_PLATFORM": "linux/arm64"}, clear=False)
        configured.start()
        self.addCleanup(configured.stop)

    def test_command_requires_digest_pinned_image_and_pull_never(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner, schema, instructions = [root / name for name in
                                             ("runner.py", "schema.json", "instructions.txt")]
            prompt, image = root / "prompt.txt", root / "image.png"
            workspace, ipc, host_repo = root / "workspace", root / "ipc", root / "host-repo"
            for path in (runner, schema, instructions, prompt, image):
                path.write_text("x", encoding="utf-8")
            for path in (workspace, ipc, host_repo):
                path.mkdir()
            env = {
                "AGENT_INTERFACE_DOCKER_RUNNER": str(runner),
                "AGENT_INTERFACE_DOCKER_SCHEMA": str(schema),
                "AGENT_INTERFACE_DOCKER_INSTRUCTIONS": str(instructions),
                "AGENT_INTERFACE_DOCKER_IMAGE": "test:mutable-tag",
                "AGENT_INTERFACE_DOCKER_IPC": str(ipc),
                "AGENT_INTERFACE_DOCKER_HOST_REPO": str(host_repo),
            }
            with patch.dict(os.environ, env, clear=False):
                with self.assertRaisesRegex(RuntimeError,
                                            "STOP_DOCKER_BACKEND_IMAGE_NOT_DIGEST_PINNED"):
                    backend.build_command(root / "out", prompt, image, "plain", workspace)
            self.assertFalse((host_repo / "schema.json").exists(),
                             "mutable image must be rejected before staging")

    def test_host_repo_mapping_lock_is_released_after_backend_exception(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            host_repo = root / "host-repo"
            host_repo.mkdir()
            env = os.environ.copy()
            env["AGENT_INTERFACE_DOCKER_HOST_REPO"] = str(host_repo)
            source = f"""
import sys
from pathlib import Path
sys.path.insert(0, {str(Path(__file__).parent)!r})
import docker_model_call_backend_v1 as backend
with backend._host_repo_mapping_lock():
    pass
"""
            with patch.dict(os.environ, {
                    "AGENT_INTERFACE_DOCKER_HOST_REPO": str(host_repo)}, clear=False), \
                 patch.object(backend, "_call_locked", side_effect=RuntimeError("synthetic timeout")):
                with self.assertRaisesRegex(RuntimeError, "synthetic timeout"):
                    backend.call(root / "call", "prompt", root / "image.png", "plain", root)
            probe = subprocess.run([sys.executable, "-c", source], env=env,
                                   capture_output=True, text=True, timeout=3)
            self.assertEqual(probe.returncode, 0, probe.stderr)

    def test_host_repo_mapping_lock_serializes_separate_processes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            host_repo = root / "host-repo"
            host_repo.mkdir()
            child_waiting = root / "child-waiting"
            child_entered = root / "child-entered"
            backend_entered = threading.Event()
            release_backend = threading.Event()
            source = f"""
import sys, time
from pathlib import Path
sys.path.insert(0, {str(Path(__file__).parent)!r})
import docker_model_call_backend_v1 as backend
Path({str(child_waiting)!r}).write_text('waiting')
with backend._host_repo_mapping_lock():
    Path({str(child_entered)!r}).write_text('acquired')
"""
            env = os.environ.copy()
            env["AGENT_INTERFACE_DOCKER_HOST_REPO"] = str(host_repo)
            def fake_call_locked(*_args, **_kwargs):
                backend_entered.set()
                if not release_backend.wait(timeout=5):
                    raise TimeoutError("test did not release backend call")
                return {"status": "synthetic-return"}

            with patch.dict(os.environ, {
                "AGENT_INTERFACE_DOCKER_HOST_REPO": str(host_repo)}, clear=False), \
                 patch.object(backend, "_call_locked", side_effect=fake_call_locked):
                caller = threading.Thread(target=lambda: backend.call(
                    root / "call", "prompt", root / "image.png", "plain", root))
                caller.start()
                self.assertTrue(backend_entered.wait(timeout=3))
                child = subprocess.Popen([sys.executable, "-c", source], env=env)
                try:
                    deadline = time.monotonic() + 3
                    while not child_waiting.exists() and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertTrue(child_waiting.exists(), "child did not start lock attempt")
                    time.sleep(0.2)
                    self.assertFalse(child_entered.exists(),
                                     "second process entered during the active model call")
                    release_backend.set()
                    caller.join(timeout=3)
                    self.assertFalse(caller.is_alive(), "backend call did not release its lock")
                    self.assertEqual(child.wait(timeout=3), 0)
                    self.assertTrue(child_entered.exists())
                finally:
                    release_backend.set()
                    if caller.is_alive():
                        caller.join(timeout=3)
                    if child.poll() is None:
                        child.kill()
                        child.wait(timeout=3)

    def test_no_image_schema_preflight_has_an_explicit_backend_entrypoint(self):
        self.assertTrue(
            callable(getattr(backend, "preflight_schema", None)),
            "schema endpoint preflight must use the same Docker/host-IPC backend",
        )

    def test_model_command_selects_schema_and_instructions_for_each_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runner = root / "runner.py"
            plain_schema = root / "plain.json"
            compiled_schema = root / "compiled.json"
            plain_instructions = root / "plain.txt"
            compiled_instructions = root / "compiled.txt"
            prompt = root / "prompt.txt"
            image = root / "image.png"
            workspace = root / "workspace"
            ipc = root / "ipc"
            for path in (runner, plain_schema, compiled_schema, plain_instructions,
                         compiled_instructions, prompt, image):
                path.write_text("x", encoding="utf-8")
            workspace.mkdir()
            ipc.mkdir()
            host_repo = root / "host-repo"
            host_repo.mkdir()
            env = {
                "AGENT_INTERFACE_DOCKER_RUNNER": str(runner),
                "AGENT_INTERFACE_DOCKER_IMAGE": "pinned-runtime@sha256:" + "c" * 64,
                "AGENT_INTERFACE_DOCKER_IPC": str(ipc),
                "AGENT_INTERFACE_DOCKER_HOST_REPO": str(host_repo),
                "AGENT_INTERFACE_DOCKER_SCHEMA": str(plain_schema),
                "AGENT_INTERFACE_DOCKER_INSTRUCTIONS": str(plain_instructions),
                "AGENT_INTERFACE_DOCKER_SCHEMA_PLAIN": str(plain_schema),
                "AGENT_INTERFACE_DOCKER_SCHEMA_COMPILED": str(compiled_schema),
                "AGENT_INTERFACE_DOCKER_INSTRUCTIONS_PLAIN": str(plain_instructions),
                "AGENT_INTERFACE_DOCKER_INSTRUCTIONS_COMPILED": str(compiled_instructions),
            }
            with patch.dict(os.environ, env, clear=False):
                plain = backend.build_command(root / "out-plain", prompt, image,
                                              "plain", workspace)
                compiled = backend.build_command(root / "out-compiled", prompt, image,
                                                 "compiled", workspace)
            for command in (plain, compiled):
                self.assertIn("--pull=never", command)
                self.assertEqual(command[command.index("--platform") + 1], "linux/arm64")
            self.assertIn(f"{plain_schema.resolve()}:/repo/schema.json:ro", plain)
            self.assertIn(f"{plain_instructions.resolve()}:/repo/instructions.txt:ro", plain)
            self.assertIn(f"{compiled_schema.resolve()}:/repo/schema.json:ro", compiled)
            self.assertIn(f"{compiled_instructions.resolve()}:/repo/instructions.txt:ro", compiled)
            self.assertEqual((host_repo / "schema.json").resolve(), compiled_schema.resolve())
            self.assertEqual((host_repo / "workspace").resolve(), workspace.resolve())

    def test_command_publishes_auditable_host_repo_mapping(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runner, schema, instructions, prompt, image = [
                root / name for name in ("runner.py", "schema.json", "instructions.txt",
                                         "prompt.txt", "image.png")]
            workspace, ipc, host_repo = [root / name for name in
                                          ("workspace", "ipc", "host-repo")]
            for path in (runner, schema, instructions, prompt, image):
                path.write_text("x", encoding="utf-8")
            for path in (workspace, ipc, host_repo):
                path.mkdir()
            out = root / "out"
            out.mkdir()
            env = {"AGENT_INTERFACE_DOCKER_RUNNER": str(runner),
                   "AGENT_INTERFACE_DOCKER_IMAGE": "pinned@sha256:" + "a" * 64,
                   "AGENT_INTERFACE_DOCKER_IPC": str(ipc),
                   "AGENT_INTERFACE_DOCKER_HOST_REPO": str(host_repo),
                   "AGENT_INTERFACE_DOCKER_SCHEMA": str(schema),
                   "AGENT_INTERFACE_DOCKER_INSTRUCTIONS": str(instructions)}
            with patch.dict(os.environ, env, clear=False):
                backend.build_command(out, prompt, image, "plain", workspace)
            mapping = json.loads((out / "host-path-map.json").read_text())
            self.assertEqual(mapping["paths"]["schema"]["host_path"], str(schema.resolve()))
            self.assertEqual(mapping["paths"]["image"]["host_path"], str(image.resolve()))
            self.assertEqual(mapping["paths"]["workspace"]["host_path"], str(workspace.resolve()))

    def test_host_repo_mapping_rejects_a_retargeted_schema_link(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = self._preflight_inputs(root)
            out = root / "preflight"
            out.mkdir()
            (out / "prompt.txt").write_text("probe", encoding="utf-8")
            runner = paths["runner.py"]
            env = {"AGENT_INTERFACE_DOCKER_HOST_REPO": str(paths["host-repo"]),
                   "AGENT_INTERFACE_DOCKER_RUNNER": str(runner)}
            with patch.dict(os.environ, env, clear=False):
                backend._stage_host_repo(
                    out, runner, paths["schema.json"], paths["instructions.txt"],
                    out / "prompt.txt", paths["workspace"])
                wrong = root / "wrong-schema.json"
                wrong.write_text("{}", encoding="utf-8")
                link = paths["host-repo"] / "schema.json"
                link.unlink()
                link.symlink_to(wrong)
                with self.assertRaisesRegex(ValueError, "schema"):
                    backend._verify_host_repo_mapping(
                        out, paths["schema.json"], paths["instructions.txt"],
                        paths["workspace"], None)

    def _preflight_inputs(self, root):
        paths = {name: root / name for name in
                 ("runner.py", "schema.json", "instructions.txt", "workspace", "ipc",
                  "host-repo")}
        for name in ("runner.py", "schema.json", "instructions.txt"):
            paths[name].write_text("{}", encoding="utf-8")
        paths["schema.json"].write_text(json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "const": {"compatible": True},
        }), encoding="utf-8")
        for name in ("workspace", "ipc", "host-repo"):
            paths[name].mkdir()
        return paths

    def _preflight_runner_result(self, root, ipc, schema, instructions,
                                 *, response='{"compatible": true}'):
        request_id = "a" * 32
        runner = root / "runner"
        runner.mkdir()
        events = [
            {"type": "thread.started", "thread_id": "schema-call-01"},
            {"type": "item.completed", "item": {
                "type": "agent_message", "text": response}},
            {"type": "turn.completed", "usage": {
                "input_tokens": 41, "cached_input_tokens": 2,
                "output_tokens": 3, "reasoning_output_tokens": 0}},
        ]
        event_text = "".join(json.dumps(row) + "\n" for row in events)
        (runner / "events.jsonl").write_text(event_text, encoding="utf-8")
        (runner / "process.json").write_text(json.dumps({
            "exit_code": 0, "requested_model": "gpt-5.6-luna",
            "requested_effort": "low", "mode": "handle",
            "request_id": request_id,
        }), encoding="utf-8")
        (ipc / f"{request_id}.request.json").write_text(json.dumps({
            "request_id": request_id, "mode": "handle",
            "image": None, "authority_granted": False,
            "schema": "/repo/schema.json", "working": "/repo/workspace",
            "schema_sha256": hashlib.sha256(schema.read_bytes()).hexdigest(),
            "instructions_sha256": hashlib.sha256(
                instructions.read_bytes()).hexdigest(),
        }), encoding="utf-8")
        (ipc / f"{request_id}.response.jsonl").write_text(event_text, encoding="utf-8")
        (ipc / f"{request_id}.broker.json").write_text(json.dumps({
            "request_id": request_id, "returncode": 0,
            "boundary": "host-local-codex-exe", "authority_granted": False,
            "resolved_paths": {"schema": str(schema.resolve()),
                               "working": str((root.parent / "workspace").resolve()),
                               "image": None},
        }), encoding="utf-8")

    def test_schema_preflight_uses_no_image_handle_request_and_network_is_disabled(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = self._preflight_inputs(root)
            (root / "out").mkdir()
            (root / "out" / "prompt.txt").write_text("schema probe", encoding="utf-8")
            env = {
                "AGENT_INTERFACE_DOCKER_RUNNER": str(paths["runner.py"]),
                "AGENT_INTERFACE_DOCKER_IMAGE": "pinned-runtime@sha256:" + "a" * 64,
                "AGENT_INTERFACE_DOCKER_IPC": str(paths["ipc"]),
                "AGENT_INTERFACE_DOCKER_HOST_REPO": str(paths["host-repo"]),
                "DOCKER": "/usr/bin/docker",
            }
            with patch.dict(os.environ, env, clear=False):
                command = backend.build_preflight_command(
                    root / "out", paths["schema.json"], paths["instructions.txt"],
                    paths["workspace"])
            self.assertIn("--network", command)
            self.assertEqual(command[command.index("--network") + 1], "none")
            self.assertIn("--pull=never", command)
            self.assertEqual(command[command.index("--platform") + 1], "linux/arm64")
            self.assertIn("handle", command)
            self.assertNotIn("coordinate", command)
            self.assertNotIn("/repo/image.png", command)
            self.assertEqual(command[-1], "/repo/schema.json")

    def test_schema_preflight_returns_fresh_call_id_usage_and_zero_images(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = self._preflight_inputs(root)
            out = root / "preflight"
            env = {
                "AGENT_INTERFACE_DOCKER_RUNNER": str(paths["runner.py"]),
                "AGENT_INTERFACE_DOCKER_IMAGE": "pinned-runtime@sha256:" + "a" * 64,
                "AGENT_INTERFACE_DOCKER_IPC": str(paths["ipc"]),
                "AGENT_INTERFACE_DOCKER_HOST_REPO": str(paths["host-repo"]),
            }

            def fake_docker(*args, **kwargs):
                self.assertEqual(kwargs["timeout"], 90)
                self._preflight_runner_result(
                    out, paths["ipc"], paths["schema.json"], paths["instructions.txt"])
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch.dict(os.environ, env, clear=False), \
                 patch("docker_model_call_backend_v1.subprocess.run",
                       side_effect=fake_docker) as run:
                result = backend.preflight_schema(
                    out, paths["schema.json"], paths["instructions.txt"],
                    paths["workspace"])
            run.assert_called_once()
            self.assertEqual(result["call_id"], "schema-call-01")
            self.assertEqual(result["usage"]["input_tokens"], 41)
            self.assertEqual(result["model_visible_images"], 0)
            self.assertTrue(result["fresh"])
            retained_ipc = out / "host-ipc"
            self.assertTrue((retained_ipc / "request.json").is_file())
            self.assertTrue((retained_ipc / "broker.json").is_file())
            self.assertEqual(
                (retained_ipc / "response.jsonl").read_bytes(),
                (out / "runner" / "events.jsonl").read_bytes(),
            )

    def test_schema_preflight_timeout_is_terminal_and_does_not_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = self._preflight_inputs(root)
            out = root / "preflight"
            env = {
                "AGENT_INTERFACE_DOCKER_RUNNER": str(paths["runner.py"]),
                "AGENT_INTERFACE_DOCKER_IMAGE": "pinned-runtime@sha256:" + "a" * 64,
                "AGENT_INTERFACE_DOCKER_IPC": str(paths["ipc"]),
                "AGENT_INTERFACE_DOCKER_HOST_REPO": str(paths["host-repo"]),
            }
            with patch.dict(os.environ, env, clear=False), \
                 patch("docker_model_call_backend_v1.subprocess.run",
                       side_effect=subprocess.TimeoutExpired(["docker"], 90)) as run:
                with self.assertRaisesRegex(RuntimeError, "STOP_DOCKER_PREFLIGHT_TIMEOUT"):
                    backend.preflight_schema(
                        out, paths["schema.json"], paths["instructions.txt"],
                        paths["workspace"])
            run.assert_called_once()
            receipt = json.loads((out / "preflight-result.json").read_text())
            self.assertFalse(receipt["retry_performed"])
            self.assertEqual(receipt["container_state"], "unknown")
            self.assertEqual(receipt["host_model_state"], "unknown")

    def test_schema_preflight_rejects_schema_invalid_answer_without_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = self._preflight_inputs(root)
            out = root / "preflight"
            env = {
                "AGENT_INTERFACE_DOCKER_RUNNER": str(paths["runner.py"]),
                "AGENT_INTERFACE_DOCKER_IMAGE": "pinned-runtime@sha256:" + "a" * 64,
                "AGENT_INTERFACE_DOCKER_IPC": str(paths["ipc"]),
                "AGENT_INTERFACE_DOCKER_HOST_REPO": str(paths["host-repo"]),
            }

            def fake_docker(*args, **kwargs):
                self._preflight_runner_result(
                    out, paths["ipc"], paths["schema.json"], paths["instructions.txt"],
                    response='{"compatible": false}')
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch.dict(os.environ, env, clear=False), \
                 patch("docker_model_call_backend_v1.subprocess.run",
                       side_effect=fake_docker) as run:
                with self.assertRaisesRegex(RuntimeError, "STOP_DOCKER_PREFLIGHT_OUTPUT"):
                    backend.preflight_schema(
                        out, paths["schema.json"], paths["instructions.txt"],
                        paths["workspace"])
            run.assert_called_once()
            receipt = json.loads((out / "preflight-result.json").read_text())
            self.assertEqual(receipt["validation"]["status"], "STOP_SCHEMA_OUTPUT_INVALID")
            self.assertFalse(receipt["retry_performed"])

    def test_schema_preflight_rejects_wrong_model_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = self._preflight_inputs(root)
            out = root / "preflight"
            env = {
                "AGENT_INTERFACE_DOCKER_RUNNER": str(paths["runner.py"]),
                "AGENT_INTERFACE_DOCKER_IMAGE": "pinned-runtime@sha256:" + "a" * 64,
                "AGENT_INTERFACE_DOCKER_IPC": str(paths["ipc"]),
                "AGENT_INTERFACE_DOCKER_HOST_REPO": str(paths["host-repo"]),
            }

            def fake_docker(*args, **kwargs):
                self._preflight_runner_result(
                    out, paths["ipc"], paths["schema.json"], paths["instructions.txt"])
                receipt = out / "runner" / "process.json"
                value = json.loads(receipt.read_text())
                value["requested_model"] = "unexpected-model"
                receipt.write_text(json.dumps(value))
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch.dict(os.environ, env, clear=False), \
                 patch("docker_model_call_backend_v1.subprocess.run",
                       side_effect=fake_docker) as run:
                with self.assertRaisesRegex(RuntimeError, "STOP_DOCKER_PREFLIGHT_OUTPUT"):
                    backend.preflight_schema(
                        out, paths["schema.json"], paths["instructions.txt"],
                        paths["workspace"])
            run.assert_called_once()
            self.assertEqual(json.loads((out / "preflight-result.json").read_text())[
                "status"], "STOP_DOCKER_PREFLIGHT_OUTPUT")

    def test_task_model_call_retains_matching_host_ipc_receipts(self):
        from integrated_efficiency_model_v1 import CONTRACTS
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "model-call"
            image = root / "observation.png"
            image.write_bytes(b"frozen image bytes")
            workspace = root / "workspace"
            workspace.mkdir()
            ipc = root / "ipc"
            ipc.mkdir()
            instructions = root / "instructions.txt"
            instructions.write_text("model instruction", encoding="utf-8")
            runner_source = root / "runner.py"
            runner_source.write_text("# synthetic runner", encoding="utf-8")
            host_repo = root / "host-repo"
            host_repo.mkdir()
            schema = CONTRACTS["plain"][0]
            request_id = "b" * 32
            answer = {
                "format": "plain-form-points-v1",
                "field": {"point_space": "source_observation_pixels",
                          "point": {"x": 10, "y": 20}},
                "submit": {"point_space": "source_observation_pixels",
                           "point": {"x": 30, "y": 40}},
            }
            events = [
                {"type": "thread.started", "thread_id": "model-call-01"},
                {"type": "item.completed", "item": {
                    "type": "agent_message", "text": json.dumps(answer)}},
                {"type": "turn.completed", "usage": {
                    "input_tokens": 9, "output_tokens": 4}},
            ]
            event_text = "".join(json.dumps(row) + "\n" for row in events)
            env = {
                "AGENT_INTERFACE_DOCKER_RUNNER": str(runner_source),
                "AGENT_INTERFACE_DOCKER_IMAGE": "pinned-runtime@sha256:" + "a" * 64,
                "AGENT_INTERFACE_DOCKER_SCHEMA": str(schema),
                "AGENT_INTERFACE_DOCKER_INSTRUCTIONS": str(instructions),
                "AGENT_INTERFACE_DOCKER_IPC": str(ipc),
                "AGENT_INTERFACE_DOCKER_HOST_REPO": str(host_repo),
            }

            def fake_docker(*args, **kwargs):
                runner = output / "runner"
                runner.mkdir(parents=True)
                (runner / "events.jsonl").write_text(event_text, encoding="utf-8")
                (runner / "process.json").write_text(json.dumps({
                    "started_ns": 10, "exited_ns": 20,
                    "requested_model": "gpt-5.6-luna", "requested_effort": "low",
                    "mode": "coordinate", "request_id": request_id,
                }), encoding="utf-8")
                request = {
                    "request_id": request_id, "mode": "coordinate",
                    "image": "/repo/image.png", "authority_granted": False,
                    "schema": "/repo/schema.json", "working": "/repo/workspace",
                    "schema_sha256": hashlib.sha256(schema.read_bytes()).hexdigest(),
                    "instructions_sha256": hashlib.sha256(instructions.read_bytes()).hexdigest(),
                    "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                }
                (ipc / f"{request_id}.request.json").write_text(json.dumps(request))
                (ipc / f"{request_id}.response.jsonl").write_text(event_text)
                (ipc / f"{request_id}.broker.json").write_text(json.dumps({
                    "request_id": request_id, "returncode": 0,
                    "boundary": "host-local-codex-exe", "authority_granted": False,
                    "resolved_paths": {"schema": str(schema.resolve()),
                                       "working": str(workspace.resolve()),
                                       "image": str(image.resolve())},
                }))
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch.dict(os.environ, env, clear=False), \
                 patch("docker_model_call_backend_v1.subprocess.run",
                       side_effect=fake_docker) as run:
                result = call(output, "prompt", image, "plain", workspace)
            run.assert_called_once()
            self.assertEqual(result["call_id"], "model-call-01")
            self.assertNotIn("host_ipc", result)
            retained = output / "host-ipc"
            self.assertTrue((retained / "request.json").is_file())
            self.assertTrue((retained / "broker.json").is_file())
            self.assertEqual((retained / "response.jsonl").read_text(), event_text)
            ipc_receipt = json.loads((retained / "receipt.json").read_text())
            self.assertEqual(ipc_receipt["request_id"], request_id)
            self.assertEqual(ipc_receipt["host_cli_returncode"], 0)

    def test_real_local_client_timeout_reaps_only_its_direct_child(self):
        children = []
        popen = subprocess.Popen
        def tracked_popen(*args, **kwargs):
            child = popen(*args, **kwargs)
            children.append(child)
            return child

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'call'
            # Exercise subprocess.run's real timeout/kill/wait path using only
            # an owned Python sleeper, never Docker or a host-model process.
            command = [sys.executable, '-c', 'import time; time.sleep(30)']
            with patch.dict(os.environ, {
                    'AGENT_INTERFACE_DOCKER_SCHEMA': 'unused',
                    'AGENT_INTERFACE_DOCKER_HOST_REPO': str(temp)}), \
                 patch('docker_model_call_backend_v1.build_command', return_value=command), \
                 patch('docker_model_call_backend_v1.CLIENT_TIMEOUT_SECONDS', 0.2), \
                 patch('subprocess.Popen', side_effect=tracked_popen):
                try:
                    with self.assertRaisesRegex(RuntimeError, 'STOP_DOCKER_BACKEND_TIMEOUT'):
                        call(root, 'prompt', Path(temp)/'image', 'plain', Path(temp))
                    self.assertEqual(len(children), 1)
                    self.assertIsNotNone(children[0].returncode)
                    receipt = json.loads((root/'client-result.json').read_text())
                    self.assertEqual(receipt['container_state'], 'unknown')
                    self.assertEqual(receipt['host_model_state'], 'unknown')
                    self.assertFalse((root/'result.json').exists())
                finally:
                    for child in children:
                        if child.poll() is None:
                            child.kill()
                        child.wait(timeout=5)

    def test_client_timeout_retains_uncertainty_without_retry_or_parse(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'call'
            def expire(*args, **kwargs):
                self.assertEqual(kwargs['timeout'], 90)
                self.assertTrue((root/'client-attempt.json').is_file())
                raise subprocess.TimeoutExpired(['inert'], 90,
                    output=b'x'*2500+b'last', stderr=b'partial error')
            with patch.dict(os.environ, {'AGENT_INTERFACE_DOCKER_SCHEMA': 'unused',
                                         'AGENT_INTERFACE_MODEL_BACKEND': 'legacy',
                                         'AGENT_INTERFACE_DOCKER_HOST_REPO': str(temp)}), \
                 patch('docker_model_call_backend_v1.build_command', return_value=['inert']), \
                 patch('docker_model_call_backend_v1.subprocess.run', side_effect=expire) as run, \
                 patch('integrated_efficiency_model_v1.parse') as parse:
                with self.assertRaisesRegex(RuntimeError, 'STOP_DOCKER_BACKEND_TIMEOUT'):
                    call(root, 'prompt', Path(temp)/'image', 'plain', Path(temp))
                run.assert_called_once()
                parse.assert_not_called()
            receipt = json.loads((root/'client-result.json').read_text())
            self.assertEqual(receipt['container_state'], 'unknown')
            self.assertEqual(receipt['host_model_state'], 'unknown')
            self.assertFalse(receipt['retry_performed'])
            self.assertIsNone(receipt['returncode'])
            self.assertEqual(len((root/'runner-stdout.txt').read_text()), 2000)
            self.assertTrue((root/'runner-stdout.txt').read_text().endswith('last'))
            self.assertFalse((root/'result.json').exists())

    def test_call_validates_output_before_semantic_parse_without_retry(self):
        for answer, valid in (({"answer": "ok"}, True), ({"answer": "wrong"}, False)):
            with self.subTest(answer=answer), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                schema = root / 'schema.json'
                schema.write_text(json.dumps({
                    '$schema': 'https://json-schema.org/draft/2020-12/schema',
                    'const': {'answer': 'ok'},
                }), encoding='utf-8')
                output = root / 'call'

                def runner(*args, **kwargs):
                    retained = output / 'runner'
                    retained.mkdir()
                    (retained / 'process.json').write_text('{}')
                    rows = [
                        {'type': 'turn.completed', 'usage': {'input_tokens': 7}},
                        {'type': 'item.completed', 'item': {
                            'type': 'agent_message', 'text': json.dumps(answer)}},
                    ]
                    (retained / 'events.jsonl').write_text(
                        ''.join(json.dumps(row) + '\n' for row in rows))
                    return SimpleNamespace(returncode=0, stdout='runner output', stderr='')

                with patch.dict(os.environ, {'AGENT_INTERFACE_DOCKER_SCHEMA': str(schema),
                                             'AGENT_INTERFACE_MODEL_BACKEND': 'legacy',
                                             'AGENT_INTERFACE_DOCKER_HOST_REPO': str(root)}), \
                     patch('docker_model_call_backend_v1.build_command', return_value=['inert']), \
                     patch('docker_model_call_backend_v1.subprocess.run', side_effect=runner) as run, \
                     patch('integrated_efficiency_model_v1.parse', return_value={'grounding': 'validated'}) as parse:
                    if valid:
                        self.assertEqual(call(output, 'prompt', root/'image', 'plain', root),
                                         {'grounding': 'validated'})
                        parse.assert_called_once_with(output/'runner', 'plain')
                        self.assertEqual(json.loads((output/'result.json').read_text()),
                                         {'grounding': 'validated'})
                    else:
                        with self.assertRaisesRegex(RuntimeError, 'STOP_SCHEMA_OUTPUT_INVALID'):
                            call(output, 'prompt', root/'image', 'plain', root)
                        parse.assert_not_called()
                        self.assertFalse((output/'result.json').exists())
                    run.assert_called_once()
                validation = json.loads((output/'schema-validation.json').read_text())
                self.assertEqual(validation['status'], 'PASS' if valid else 'STOP_SCHEMA_OUTPUT_INVALID')
                self.assertEqual((output/'runner-stdout.txt').read_text(), 'runner output')

    def test_actual_semantic_parser_preserves_grounding_and_usage(self):
        from integrated_efficiency_model_v1 import CONTRACTS
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'call'
            answer = {'format': 'plain-form-points-v1',
                      'field': {'point_space': 'source_observation_pixels', 'point': {'x': 10, 'y': 20}},
                      'submit': {'point_space': 'source_observation_pixels', 'point': {'x': 30, 'y': 40}}}
            def runner(*args, **kwargs):
                retained = root/'runner'; retained.mkdir()
                rows = [{'type': 'thread.started', 'thread_id': 'synthetic-call'},
                        {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': json.dumps(answer)}},
                        {'type': 'turn.completed', 'usage': {'input_tokens': 7, 'output_tokens': 3}}]
                (retained/'events.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
                (retained/'process.json').write_text(json.dumps({
                    'started_ns': 10, 'exited_ns': 30, 'requested_model': 'synthetic',
                    'requested_effort': 'low'}))
                return SimpleNamespace(returncode=0, stdout='', stderr='')
            with patch.dict(os.environ, {
                    'AGENT_INTERFACE_DOCKER_SCHEMA': str(CONTRACTS['plain'][0]),
                    'AGENT_INTERFACE_DOCKER_HOST_REPO': temp}), \
                 patch('docker_model_call_backend_v1.build_command', return_value=['inert']), \
                 patch('docker_model_call_backend_v1.subprocess.run', side_effect=runner) as run:
                result = call(root, 'prompt', Path(temp)/'image', 'plain', Path(temp))
                run.assert_called_once()
            self.assertEqual(result['grounding'], {'field_point': [10,20], 'submit_point': [30,40]})
            self.assertEqual(result['usage'], {'input_tokens': 7, 'output_tokens': 3})
            self.assertEqual(result['call_id'], 'synthetic-call')
            self.assertEqual(result['runner_ns'], 20)
            self.assertIsNone(result['cost'])

    def test_compiled_contract_passes_schema_gate_and_semantic_parser(self):
        from integrated_efficiency_model_v1 import CONTRACTS
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'call'
            answer = {
                'format': 'compiled-form-grounding-v1',
                'field': {'point_space': 'source_observation_pixels',
                          'point': {'x': 10, 'y': 20},
                          'motion_model': 'surface_origin_translation'},
                'submit': {'point_space': 'source_observation_pixels',
                           'point': {'x': 30, 'y': 40},
                           'motion_model': 'surface_origin_translation'},
                'method': {
                    'first_action': 'enter_exact_token',
                    'continue_when': 'field_pixels_changed_and_submit_revalidated',
                    'second_action': 'activate_submit',
                    'complete_when': 'submission_pixels_changed_then_independent_score',
                },
            }
            def runner(*args, **kwargs):
                retained = root/'runner'; retained.mkdir()
                rows = [
                    {'type': 'thread.started', 'thread_id': 'synthetic-compiled-call'},
                    {'type': 'item.completed', 'item': {
                        'type': 'agent_message', 'text': json.dumps(answer)}},
                    {'type': 'turn.completed', 'usage': {
                        'input_tokens': 11, 'output_tokens': 9}},
                ]
                (retained/'events.jsonl').write_text(
                    ''.join(json.dumps(row)+'\n' for row in rows))
                (retained/'process.json').write_text(json.dumps({
                    'started_ns': 100, 'exited_ns': 150,
                    'requested_model': 'synthetic', 'requested_effort': 'low'}))
                return SimpleNamespace(returncode=0, stdout='', stderr='')

            with patch.dict(os.environ, {
                    'AGENT_INTERFACE_DOCKER_SCHEMA': str(CONTRACTS['compiled'][0]),
                    'AGENT_INTERFACE_DOCKER_HOST_REPO': temp}), \
                 patch('docker_model_call_backend_v1.build_command', return_value=['inert']), \
                 patch('docker_model_call_backend_v1.subprocess.run', side_effect=runner) as run:
                result = call(root, 'prompt', Path(temp)/'image', 'compiled', Path(temp))
                run.assert_called_once()

            self.assertEqual(json.loads((root/'schema-validation.json').read_text())['status'], 'PASS')
            self.assertEqual(result['grounding']['field_point'], [10, 20])
            self.assertEqual(result['grounding']['submit_point'], [30, 40])
            self.assertEqual(result['grounding']['method'], answer['method'])
            self.assertEqual(result['usage'], {'input_tokens': 11, 'output_tokens': 9})
            self.assertEqual(result['call_id'], 'synthetic-compiled-call')
            self.assertEqual(result['runner_ns'], 50)

    def test_call_owns_prompt_creation_and_builder_owns_output_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'call'

            def inspect_call(out, prompt_path, image, contract, workspace):
                self.assertTrue(out.is_dir())
                self.assertEqual((out / 'prompt.txt').read_text(), 'prompt')
                return ['inert']

            with patch.dict(os.environ, {
                    'AGENT_INTERFACE_DOCKER_SCHEMA': 'unused',
                    'AGENT_INTERFACE_DOCKER_HOST_REPO': temp}), \
                 patch('docker_model_call_backend_v1.build_command',
                       side_effect=inspect_call), \
                 patch('docker_model_call_backend_v1.subprocess.run',
                       return_value=SimpleNamespace(returncode=1, stdout='', stderr='')) as run:
                with self.assertRaisesRegex(RuntimeError, 'STOP_DOCKER_BACKEND_RUNNER:1'):
                    call(root, 'prompt', Path(temp) / 'image', 'plain', Path(temp))
            run.assert_called_once()

    def test_missing_mount_stops_before_docker(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); prompt=root/'p'; image=root/'i'; workspace=root/'w'; ipc=root/'ipc'
            prompt.write_text('x'); image.write_text('x'); workspace.mkdir(); ipc.mkdir()
            values={'AGENT_INTERFACE_DOCKER_RUNNER':str(root/'missing-runner'),'AGENT_INTERFACE_DOCKER_SCHEMA':str(prompt),'AGENT_INTERFACE_DOCKER_INSTRUCTIONS':str(prompt),'AGENT_INTERFACE_DOCKER_IMAGE':'test@sha256:'+'b'*64,'AGENT_INTERFACE_DOCKER_IPC':str(ipc),'AGENT_INTERFACE_DOCKER_HOST_REPO':str(root)}
            old={k:os.environ.get(k) for k in values}
            os.environ.update(values)
            try:
                with self.assertRaises(FileNotFoundError):
                    build_command(root/'out', prompt, image, 'compiled', workspace)
            finally:
                for k,v in old.items():
                    if v is None: os.environ.pop(k,None)
                    else: os.environ[k]=v

    def test_unconfigured_stops_before_docker(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); prompt=root/'p'; image=root/'i'; workspace=root/'w'; ipc=root/'ipc'
            for p in (prompt,image,workspace,ipc):
                if p.suffix: p.write_text('x')
                else: p.mkdir()
            with self.assertRaisesRegex(RuntimeError, 'STOP_DOCKER_BACKEND_UNCONFIGURED'):
                build_command(root/'out', prompt, image, 'compiled', workspace)

    def test_command_requires_explicit_image_and_ipc(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); prompt=root/'p'; image=root/'i'; workspace=root/'w'; ipc=root/'ipc'
            prompt.write_text('x'); image.write_text('x'); workspace.mkdir(); ipc.mkdir()
            values={'AGENT_INTERFACE_DOCKER_RUNNER':str(prompt),'AGENT_INTERFACE_DOCKER_SCHEMA':str(prompt),'AGENT_INTERFACE_DOCKER_INSTRUCTIONS':str(prompt),'AGENT_INTERFACE_DOCKER_IMAGE':'test@sha256:'+'b'*64,'AGENT_INTERFACE_DOCKER_IPC':str(ipc),'AGENT_INTERFACE_DOCKER_HOST_REPO':str(root)}
            old={k:os.environ.get(k) for k in values}
            os.environ.update(values)
            try:
                command=build_command(root/'out', prompt, image, 'compiled', workspace)
                self.assertIn('test@sha256:' + 'b' * 64, command)
                self.assertIn("HOST_MODEL_IPC_DIR=/ipc", command)
                if hasattr(os, "getuid") and hasattr(os, "getgid"):
                    self.assertIn(f"HOST_MODEL_IPC_OWNER_UID={os.getuid()}", command)
                    self.assertIn(f"HOST_MODEL_IPC_OWNER_GID={os.getgid()}", command)
                self.assertIn('coordinate', command)
            finally:
                for k,v in old.items():
                    if v is None: os.environ.pop(k,None)
                    else: os.environ[k]=v

if __name__=='__main__': unittest.main()
