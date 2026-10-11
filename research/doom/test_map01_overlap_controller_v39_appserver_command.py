"""Runner command configuration tests for the MAP01 V39 controller."""
import json
import os
import subprocess
import tempfile
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
LIVE_CONTROL = HERE.parent / "live_control"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(LIVE_CONTROL))

import map01_overlap_controller_v39 as controller


class AppServerCommandTests(unittest.TestCase):
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
        self.assertIn("mcp_servers.sample_server.enabled=false", command)
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

    def test_direct_codex_command_initializes_with_an_isolated_profile(self):
        if os.name != "nt":
            self.skipTest("direct executable smoke test requires Windows")
        executable = os.environ.get("AGENT_INTERFACE_CODEX_APP_SERVER_EXE")
        if not executable or not Path(executable).is_file():
            self.skipTest("codex.exe not available for handshake smoke test")

        with tempfile.TemporaryDirectory(prefix="v39-codex-home-") as codex_home:
            Path(codex_home, "config.toml").write_text(
                '[mcp_servers."probe"]\nenabled = true\ncommand = "py"\nargs = []\n',
                encoding="utf-8")
            with patch.dict(os.environ, {
                    "CODEX_HOME": codex_home,
                    "AGENT_INTERFACE_CODEX_APP_SERVER_EXE": executable,
            }):
                process = subprocess.Popen(
                    controller.app_server_command(), stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    encoding="utf-8", errors="replace", bufsize=1)
                stdout_lines = []
                reader = threading.Thread(
                    target=lambda: stdout_lines.append(process.stdout.readline()),
                    daemon=True)
                reader.start()
                try:
                    process.stdin.write(json.dumps({
                        "method": "initialize", "id": 1,
                        "params": {
                            "clientInfo": {
                                "name": "agent-interface-smoke-test",
                                "title": "Agent Interface", "version": "1",
                            },
                            "capabilities": {
                                "experimentalApi": False,
                                "requestAttestation": False,
                            },
                        },
                    }, separators=(",", ":")) + "\n")
                    process.stdin.flush()
                    reader.join(timeout=10)
                    self.assertFalse(reader.is_alive(), "initialize response timed out")
                    self.assertTrue(stdout_lines[0], "App Server exited before initialize")
                    response = json.loads(stdout_lines[0])
                    self.assertEqual(response["id"], 1)
                    self.assertEqual(
                        Path(response["result"]["codexHome"]), Path(codex_home))
                    process.stdin.write('{"method":"initialized"}\n')
                    process.stdin.flush()
                finally:
                    process.terminate()
                    process.wait(timeout=5)
                    reader.join(timeout=1)
                    process.stdin.close()
                    process.stdout.close()
                    process.stderr.close()

    def test_legacy_node_and_cli_path_remain_the_default(self):
        with patch.dict(os.environ, {
                "CODEX_HOME": str(HERE / "nonexistent-test-codex-home")}, clear=True):
            command = controller.app_server_command()

        self.assertEqual(command[:4], [controller.NODE, controller.CLI,
                                       "app-server", "--stdio"])
        self.assertFalse(any(arg.startswith("mcp_servers.") for arg in command))


if __name__ == "__main__":
    unittest.main()
