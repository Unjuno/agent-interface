from pathlib import Path
import unittest


class HostBrokerContractTest(unittest.TestCase):
    def test_maps_container_repo_paths(self):
        from runtime.host_model_ipc_broker_v1 import host_path
        self.assertEqual(Path(host_path("/repo/runtime/a.png", Path("C:/repo"))),
                         Path("C:/repo/runtime/a.png"))
        self.assertIsNone(host_path(None, Path("C:/repo")))

    def test_maps_container_workspace_paths(self):
        from runtime.host_model_ipc_broker_v1 import host_path
        self.assertEqual(Path(host_path("/workspace/runtime/a.png", Path("C:/repo"))),
                         Path("C:/repo/runtime/a.png"))

    def _invoke_broker(self, request):
        from runtime.host_model_ipc_broker_v1 import serve

        with tempfile.TemporaryDirectory() as directory:
            ipc = Path(directory)
            (ipc / "probe.request.json").write_text(json.dumps(request), encoding="utf-8")
            with patch.dict(os.environ, {"CODEX_EXE": "codex.exe"}), \\
                 patch("runtime.host_model_ipc_broker_v1.subprocess.run") as run:
                run.return_value.stdout = "{}\\n"
                run.return_value.stderr = ""
                run.return_value.returncode = 0
                serve(ipc, Path("C:/checkout"), once=True)
                return run.call_args

    def test_forwards_repo_relative_instructions_to_cli(self):
        call = self._invoke_broker({
            "request_id": "probe", "prompt": "probe", "working": "/repo",
            "schema": "/repo/schema.json", "instructions": "/repo/instructions.txt",
            "image": None,
        })
        args = call.args[0]
        self.assertIn('model_instructions_file="C:/checkout/instructions.txt"', args)
        self.assertIn("C:/checkout/schema.json", args)

    def test_forwards_workspace_instructions_to_cli(self):
        call = self._invoke_broker({
            "request_id": "probe", "prompt": "probe", "working": "/workspace",
            "schema": "/workspace/schema.json", "instructions": "/workspace/instructions.txt",
            "image": None,
        })
        self.assertIn('model_instructions_file="C:/checkout/instructions.txt"', call.args[0])

    def test_quotes_instruction_path_as_json_config_string(self):
        call = self._invoke_broker({
            "request_id": "probe", "prompt": "probe", "working": "/repo",
            "schema": "/repo/schema.json", "instructions": '/repo/a "quoted" file.txt',
            "image": None,
        })
        self.assertIn('model_instructions_file="C:/checkout/a \\"quoted\\" file.txt"',
                      call.args[0])

    def test_preserves_image_schema_and_prompt_arguments(self):
        call = self._invoke_broker({
            "request_id": "probe", "prompt": "fixed prompt", "working": "/repo",
            "schema": "/repo/schema.json", "instructions": "/repo/instructions.txt",
            "image": "/repo/input.png",
        })
        args = call.args[0]
        self.assertEqual(args[args.index("--output-schema") + 1], "C:/checkout/schema.json")
        self.assertEqual(args[args.index("--image") + 1], "C:/checkout/input.png")
        self.assertEqual(call.kwargs["input"], "fixed prompt\\n")

    def test_broker_is_non_authoritative(self):
        source = Path(__file__).with_name("host_model_ipc_broker_v1.py").read_text()
        self.assertIn('"authority_granted": False', source)

    def test_broker_has_bounded_subprocess_timeout(self):
        source = Path(__file__).with_name("host_model_ipc_broker_v1.py").read_text()
        self.assertIn("HOST_MODEL_BROKER_TIMEOUT_S", source)
        self.assertIn("TimeoutExpired", source)


if __name__ == "__main__":
    unittest.main()
