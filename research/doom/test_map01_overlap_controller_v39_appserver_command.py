"""Runner command configuration tests for the MAP01 V39 controller."""
import json
import os
import tempfile
from pathlib import Path
import sys
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

    def test_direct_codex_command_initializes_with_production_client(self):
        if os.name != "nt":
            self.skipTest("direct executable smoke test requires Windows")
        executable = os.environ.get("AGENT_INTERFACE_CODEX_APP_SERVER_EXE")
        if not executable or not Path(executable).is_file():
            self.skipTest("codex.exe not available for handshake smoke test")

        with tempfile.TemporaryDirectory(prefix="v39-codex-home-") as codex_home:
            Path(codex_home, "config.toml").write_text(
                '[mcp_servers."probe"]\nenabled = true\ncommand = "py"\nargs = []\n',
                encoding="utf-8")
            with tempfile.TemporaryDirectory(prefix="v39-journal-") as journal_dir:
                journal = Path(journal_dir, "app-server.jsonl")
                with patch.dict(os.environ, {
                        "CODEX_HOME": codex_home,
                        "AGENT_INTERFACE_CODEX_APP_SERVER_EXE": executable,
                }):
                    client = controller.CodexAppServerClient(
                        controller.app_server_command(), cwd=str(HERE),
                        journal_path=str(journal))
                    try:
                        result = client.initialize()
                    finally:
                        client.close()

                self.assertTrue(client.process.stdin.closed)
                self.assertTrue(client.process.stdout.closed)
                self.assertTrue(client.process.stderr.closed)
                self.assertEqual(Path(result["codexHome"]), Path(codex_home))
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

    def test_legacy_node_and_cli_path_remain_the_default(self):
        with patch.dict(os.environ, {
                "CODEX_HOME": str(HERE / "nonexistent-test-codex-home")}, clear=True):
            command = controller.app_server_command()

        self.assertEqual(command[:4], [controller.NODE, controller.CLI,
                                       "app-server", "--stdio"])
        self.assertFalse(any(arg.startswith("mcp_servers.") for arg in command))


if __name__ == "__main__":
    unittest.main()
