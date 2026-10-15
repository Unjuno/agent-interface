"""Runner command configuration tests for the MAP01 V39 controller."""
import json
import os
import tempfile
import time
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
LIVE_CONTROL = HERE.parent / "live_control"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(LIVE_CONTROL))

import map01_overlap_controller_v39 as controller
import codex_app_server_client_v2 as app_server_client


class AppServerCommandTests(unittest.TestCase):
    def test_wsl_windows_codex_receives_path_translated_codex_home(self):
        build_environment = getattr(
            app_server_client, "wsl_environment_for_windows_executable", None)
        self.assertIsNotNone(
            build_environment,
            "WSL interop must forward CODEX_HOME to the Windows App Server")
        source = {
            "WSL_INTEROP": "/run/WSL/123_interop",
            "CODEX_HOME": "/mnt/c/Users/example/.codex",
            "WSLENV": "KEEP_ME/u",
            "PATH": "/usr/bin",
        }
        result = build_environment(
            ["/mnt/c/Program Files/Codex/codex.exe", "app-server", "--stdio"],
            source)

        self.assertEqual(result["WSLENV"], "KEEP_ME/u:CODEX_HOME/p")
        self.assertEqual(result["CODEX_HOME"], source["CODEX_HOME"])
        self.assertEqual(result["PATH"], source["PATH"])
        self.assertEqual(source["WSLENV"], "KEEP_ME/u")

    def test_wsl_windows_codex_rejects_missing_or_windows_style_codex_home(self):
        command = ["/mnt/c/Program Files/Codex/codex.exe", "app-server", "--stdio"]
        base = {"WSL_INTEROP": "/run/WSL/123_interop"}
        for codex_home in (None, r"C:\Users\example\.codex"):
            with self.subTest(codex_home=codex_home):
                environment = dict(base)
                if codex_home is not None:
                    environment["CODEX_HOME"] = codex_home
                with self.assertRaisesRegex(
                        app_server_client.AppServerError,
                        "requires CODEX_HOME as an absolute WSL path"):
                    app_server_client.wsl_environment_for_windows_executable(
                        command, environment)

    def test_wsl_node_cli_fallback_does_not_require_windows_codex_home(self):
        command = [
            "/mnt/c/Program Files/nodejs/node.exe",
            r"C:\Users\example\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js",
            "app-server", "--stdio",
        ]
        environment = {"WSL_INTEROP": "/run/WSL/123_interop"}

        try:
            result = app_server_client.wsl_environment_for_windows_executable(
                command, environment)
        except app_server_client.AppServerError as error:
            self.fail(f"legacy Node/npm fallback was rejected: {error}")
        self.assertIsNone(result)

    def test_direct_codex_executable_disables_configured_mcps_individually(self):
        executable = str(Path(controller.__file__).resolve())
        with tempfile.TemporaryDirectory() as codex_home:
            Path(codex_home, "config.toml").write_text(
                '[mcp_servers."sample_server"]\ncommand = "ignored"\n',
                encoding="utf-8")
            with patch.dict(os.environ, {
                    "AGENT_INTERFACE_CODEX_APP_SERVER_EXE": executable,
                    "CODEX_HOME": codex_home,
            }):
                command = controller.app_server_command()

        self.assertEqual(command[:3], [executable, "app-server", "--stdio"])
        for feature in controller.DISABLED_FEATURES:
            self.assertIn(feature, command)
        self.assertIn('mcp_servers."sample_server".enabled=false', command)
        self.assertNotIn("mcp_servers={}", command)
        self.assertNotIn(controller.CLI, command)

    def test_direct_codex_command_omits_mcp_overrides_for_empty_profile(self):
        executable = str(Path(controller.__file__).resolve())
        with tempfile.TemporaryDirectory() as codex_home:
            Path(codex_home, "config.toml").write_text(
                "model = \"test\"\n", encoding="utf-8")
            with patch.dict(os.environ, {
                    "AGENT_INTERFACE_CODEX_APP_SERVER_EXE": executable,
                    "CODEX_HOME": codex_home,
            }):
                command = controller.app_server_command()
        self.assertFalse(any(arg.startswith("mcp_servers.") for arg in command))

    def test_codex_cli_path_is_used_when_explicit_override_is_absent(self):
        with tempfile.TemporaryDirectory() as codex_home:
            executable = str(Path(codex_home, "codex.exe"))
            Path(executable).write_bytes(b"test executable placeholder")
            with patch.dict(os.environ, {
                    "CODEX_HOME": codex_home,
                    "AGENT_INTERFACE_CODEX_APP_SERVER_EXE": "",
                    "CODEX_CLI_PATH": executable,
            }):
                command = controller.app_server_command()
        self.assertEqual(command[:3], [executable, "app-server", "--stdio"])

    def test_direct_codex_command_starts_thread_without_configured_mcp(self):
        if os.name != "nt":
            self.skipTest("direct executable smoke test requires Windows")
        executable = (os.environ.get("AGENT_INTERFACE_CODEX_APP_SERVER_EXE") or
                      os.environ.get("CODEX_CLI_PATH"))
        if not executable or not Path(executable).is_file():
            self.skipTest("codex.exe not available for handshake smoke test")

        with tempfile.TemporaryDirectory(prefix="v39-codex-home-") as codex_home:
            home = Path(codex_home)
            sentinel = home / "mcp-started"
            fake_server = home / "fake_mcp.py"
            fake_server.write_text(
                "import json, sys\n"
                "from pathlib import Path\n"
                "Path(sys.argv[1]).write_text('started', encoding='utf-8')\n"
                "for line in sys.stdin:\n"
                "    try: request = json.loads(line)\n"
                "    except Exception: continue\n"
                "    if request.get('method') == 'initialize':\n"
                "        print(json.dumps({'jsonrpc':'2.0','id':request.get('id'),'result':{'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'probe','version':'1'}}}), flush=True)\n"
                "    elif request.get('method') == 'tools/list':\n"
                "        print(json.dumps({'jsonrpc':'2.0','id':request.get('id'),'result':{'tools':[]}}), flush=True)\n",
                encoding="utf-8")
            config = (
                '[mcp_servers.probe]\nenabled = true\ncommand = ' +
                json.dumps(sys.executable) + '\nargs = [' +
                json.dumps(str(fake_server)) + ', ' + json.dumps(str(sentinel)) +
                ']\nstartup_timeout_sec = 3\n')
            Path(codex_home, "config.toml").write_text(config, encoding="utf-8")
            with tempfile.TemporaryDirectory(prefix="v39-journal-") as journal_dir:
                journal = Path(journal_dir, "app-server.jsonl")
                with patch.dict(os.environ, {
                        "CODEX_HOME": codex_home,
                        "AGENT_INTERFACE_CODEX_APP_SERVER_EXE": "",
                        "CODEX_CLI_PATH": executable,
                }):
                    client = controller.CodexAppServerClient(
                        controller.app_server_command(), cwd=str(HERE),
                        journal_path=str(journal))
                    try:
                        result = client.initialize()
                        thread = client.start_thread(cwd=codex_home, ephemeral=True)
                        deadline = time.monotonic() + 1
                        while time.monotonic() < deadline and not sentinel.exists():
                            time.sleep(.02)
                    finally:
                        client.close()

                self.assertTrue(client.process.stdin.closed)
                self.assertTrue(client.process.stdout.closed)
                self.assertTrue(client.process.stderr.closed)
                self.assertEqual(Path(result["codexHome"]), Path(codex_home))
                self.assertIsInstance(thread.get("thread", {}).get("id"), str)
                self.assertFalse(sentinel.exists(), "disabled fake MCP was launched")
                self.assertTrue(journal.is_file())
                rows = [json.loads(line) for line in journal.read_text(
                    encoding="utf-8").splitlines()]
                self.assertTrue(any(
                    row["direction"] == "received" and
                    row["message"].get("id") == 1 and
                    row["message"].get("result", {}).get("codexHome") == codex_home
                    for row in rows))
                self.assertTrue(any(
                    row["direction"] == "sent" and
                    row["message"].get("method") == "initialized"
                    for row in rows))
                self.assertTrue(any(
                    row["direction"] == "sent" and
                    row["message"].get("method") == "thread/start"
                    for row in rows))

    def test_legacy_node_and_cli_path_remain_the_default(self):
        with patch.dict(os.environ, {
                "CODEX_HOME": str(HERE / "nonexistent-test-codex-home")}, clear=True):
            command = controller.app_server_command()

        self.assertEqual(command[:4], [controller.NODE, controller.CLI,
                                       "app-server", "--stdio"])
        self.assertFalse(any(arg.startswith("mcp_servers.") for arg in command))


if __name__ == "__main__":
    unittest.main()
