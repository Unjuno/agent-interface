from pathlib import Path
import unittest
import hashlib
import tempfile


class HostBrokerContractTest(unittest.TestCase):
    def test_maps_container_repo_paths(self):
        from runtime.host_model_ipc_broker_v1 import host_path
        self.assertEqual(Path(host_path("/repo/runtime/a.png", Path("C:/repo"))),
                         Path("C:/repo/runtime/a.png"))
        self.assertIsNone(host_path(None, Path("C:/repo")))

    def test_broker_is_non_authoritative(self):
        source = Path(__file__).with_name("host_model_ipc_broker_v1.py").read_text()
        self.assertIn('"authority_granted": False', source)

    def test_broker_has_bounded_subprocess_timeout(self):
        source = Path(__file__).with_name("host_model_ipc_broker_v1.py").read_text()
        self.assertIn("HOST_MODEL_BROKER_TIMEOUT_S", source)
        self.assertIn("TimeoutExpired", source)

    def test_rejects_container_paths_outside_repo_mount(self):
        from runtime.host_model_ipc_broker_v1 import host_path
        for value in ("/etc/passwd", "/repo/../etc/passwd", "/repo/a/../../secret"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                host_path(value, Path("/tmp/repo"))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); repo = root / "repo"; repo.mkdir()
            outside = root / "secret"; outside.write_text("private")
            (repo / "escape").symlink_to(outside)
            with self.assertRaises(ValueError):
                host_path("/repo/escape", repo)

    def test_command_forwards_instructions_and_checks_asset_hashes(self):
        from runtime.host_model_ipc_broker_v1 import build_command
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "workspace").mkdir()
            schema = root / "schema.json"; schema.write_text('{"type":"object"}')
            instructions = root / "instructions.txt"; instructions.write_text("return JSON")
            digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            request = {"mode": "handle", "authority_granted": False,
                "schema": "/repo/schema.json", "schema_sha256": digest(schema),
                "instructions": "/repo/instructions.txt",
                "instructions_sha256": digest(instructions),
                "working": "/repo/workspace", "image": None}
            command = build_command(request, root, "codex")
            self.assertIn("model_instructions_file=" + __import__("json").dumps(str(instructions.resolve())), command)
            self.assertEqual(command[command.index("--output-schema") + 1], str(schema.resolve()))
            self.assertNotIn("--image", command)
            request["instructions_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                build_command(request, root, "codex")

    def test_rejects_authority_and_mode_image_mismatch(self):
        from runtime.host_model_ipc_broker_v1 import build_command
        request = {"mode": "handle", "authority_granted": True,
                   "schema": "/repo/s", "instructions": "/repo/i",
                   "working": "/repo/w", "image": None}
        with self.assertRaisesRegex(ValueError, "authority-bearing"):
            build_command(request, Path("/tmp"), "codex")
        request["authority_granted"] = False
        request["mode"] = "coordinate"
        with self.assertRaisesRegex(ValueError, "mode/image mismatch"):
            build_command(request, Path("/tmp"), "codex")

    def test_coordinate_command_checks_and_forwards_image(self):
        from runtime.host_model_ipc_broker_v1 import build_command
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "workspace").mkdir()
            schema = root / "schema.json"; schema.write_text('{}')
            instructions = root / "instructions.txt"; instructions.write_text("instructions")
            image = root / "frame.png"; image.write_bytes(b"bounded-test-image")
            digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            request = {"mode":"coordinate", "authority_granted":False,
                "schema":"/repo/schema.json", "schema_sha256":digest(schema),
                "instructions":"/repo/instructions.txt",
                "instructions_sha256":digest(instructions), "working":"/repo/workspace",
                "image":"/repo/frame.png", "image_sha256":digest(image)}
            command = build_command(request, root, "codex")
            self.assertEqual(command[command.index("--image") + 1], str(image.resolve()))
            request["image_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "image_sha256"):
                build_command(request, root, "codex")

    def test_refused_request_writes_a_bounded_broker_record_without_cli(self):
        import json
        from runtime.host_model_ipc_broker_v1 import serve
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ipc = root / "ipc"; repo = root / "repo"
            ipc.mkdir(); repo.mkdir()
            request = {"request_id":"refused", "authority_granted":True}
            (ipc / "refused.request.json").write_text(json.dumps(request))
            result = serve(ipc, repo, once=True)
            record = json.loads((ipc / "refused.broker.json").read_text())
            self.assertEqual(result, 1)
            self.assertEqual(record["stop_reason"], "HOST_BROKER_REQUEST_REFUSED")
            self.assertFalse(record["host_cli_invoked"])
            self.assertTrue((ipc / "refused.response.jsonl").is_file())

    def test_missing_asset_is_a_request_refusal_not_cli_failure(self):
        import json
        import os
        from unittest.mock import patch
        from runtime.host_model_ipc_broker_v1 import serve
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ipc = root / "ipc"; repo = root / "repo"
            ipc.mkdir(); repo.mkdir(); (repo / "workspace").mkdir()
            request = {"request_id":"missing-schema", "authority_granted":False,
                "mode":"handle", "schema":"/repo/missing-schema.json",
                "schema_sha256":"0" * 64, "instructions":"/repo/instructions.txt",
                "instructions_sha256":"0" * 64, "working":"/repo/workspace",
                "image":None, "prompt":"probe"}
            (ipc / "missing-schema.request.json").write_text(json.dumps(request))
            with patch.dict(os.environ, {"CODEX_EXE":"codex-not-used"}):
                result = serve(ipc, repo, once=True)
            record = json.loads((ipc / "missing-schema.broker.json").read_text())
            self.assertEqual(result, 1)
            self.assertEqual(record["stop_reason"], "HOST_BROKER_REQUEST_REFUSED")
            self.assertEqual(record["error_class"], "FileNotFoundError")
            self.assertFalse(record["host_cli_invoked"])
            self.assertFalse(record["request_validated"])
            self.assertFalse(record["host_cli_spawn_attempted"])

    def test_cli_identity_failure_is_not_an_asset_refusal_or_spawn_failure(self):
        import json
        from unittest.mock import patch
        from runtime.host_model_ipc_broker_v1 import serve
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ipc = root / "ipc"; repo = root / "repo"
            ipc.mkdir(); repo.mkdir(); (repo / "workspace").mkdir()
            schema = repo / "schema.json"; schema.write_text('{}')
            instructions = repo / "instructions.txt"; instructions.write_text("probe")
            request = {"request_id":"identity-failure", "authority_granted":False,
                "mode":"handle", "schema":"/repo/schema.json",
                "schema_sha256":hashlib.sha256(schema.read_bytes()).hexdigest(),
                "instructions":"/repo/instructions.txt",
                "instructions_sha256":hashlib.sha256(instructions.read_bytes()).hexdigest(),
                "working":"/repo/workspace", "image":None, "prompt":"probe"}
            (ipc / "identity-failure.request.json").write_text(json.dumps(request))
            with patch("runtime.host_model_ipc_broker_v1.executable_identity",
                       side_effect=FileNotFoundError("codex absent")):
                result = serve(ipc, repo, once=True)
            record = json.loads((ipc / "identity-failure.broker.json").read_text())
            self.assertEqual(result, 1)
            self.assertEqual(record["stop_reason"], "HOST_CLI_IDENTITY_UNAVAILABLE")
            self.assertTrue(record["request_validated"])
            self.assertFalse(record["host_cli_invoked"])
            self.assertFalse(record["host_cli_spawn_attempted"])

    def test_cli_spawn_oserror_is_not_reported_as_invoked(self):
        import json
        from unittest.mock import patch
        from runtime.host_model_ipc_broker_v1 import serve
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); ipc = root / "ipc"; repo = root / "repo"
            ipc.mkdir(); repo.mkdir(); (repo / "workspace").mkdir()
            schema = repo / "schema.json"; schema.write_text('{}')
            instructions = repo / "instructions.txt"; instructions.write_text("probe")
            request = {"request_id":"spawn-failure", "authority_granted":False,
                "mode":"handle", "schema":"/repo/schema.json",
                "schema_sha256":hashlib.sha256(schema.read_bytes()).hexdigest(),
                "instructions":"/repo/instructions.txt",
                "instructions_sha256":hashlib.sha256(instructions.read_bytes()).hexdigest(),
                "working":"/repo/workspace", "image":None, "prompt":"probe"}
            (ipc / "spawn-failure.request.json").write_text(json.dumps(request))
            with patch("runtime.host_model_ipc_broker_v1.executable_identity",
                       return_value={"version":"inert"}), \
                 patch("runtime.host_model_ipc_broker_v1.subprocess.run",
                       side_effect=FileNotFoundError("executable disappeared")):
                result = serve(ipc, repo, once=True)
            record = json.loads((ipc / "spawn-failure.broker.json").read_text())
            self.assertEqual(result, 1)
            self.assertEqual(record["stop_reason"], "HOST_BROKER_EXECUTABLE_UNAVAILABLE")
            self.assertTrue(record["request_validated"])
            self.assertFalse(record["host_cli_invoked"])
            self.assertTrue(record["host_cli_spawn_attempted"])

    def test_once_preserves_child_exit_and_response_without_model_call(self):
        import json
        from types import SimpleNamespace
        from unittest.mock import patch
        from runtime.host_model_ipc_broker_v1 import serve
        for code in (0, 7):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); ipc = root / 'ipc'; ipc.mkdir()
                request = {'request_id': 'fixture', 'prompt': 'fixture'}
                (ipc / 'fixture.request.json').write_text(json.dumps(request))
                with patch('runtime.host_model_ipc_broker_v1.build_command', return_value=['inert']), \
                     patch('runtime.host_model_ipc_broker_v1.executable_identity', return_value={'version': 'inert'}), \
                     patch('runtime.host_model_ipc_broker_v1.subprocess.run', return_value=SimpleNamespace(
                         returncode=code, stdout='fixture-response\n', stderr='')) as run:
                    self.assertEqual(serve(ipc, root, once=True), code)
                run.assert_called_once()
                self.assertEqual((ipc / 'fixture.response.jsonl').read_text(), 'fixture-response\n')
                record = json.loads((ipc / 'fixture.broker.json').read_text())
                self.assertEqual(record['returncode'], code)
                self.assertTrue(record['host_cli_invoked'])
                self.assertFalse(record['authority_granted'])


if __name__ == "__main__":
    unittest.main()
