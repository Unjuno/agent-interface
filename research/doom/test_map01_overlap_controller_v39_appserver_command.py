"""Runner command configuration tests for the MAP01 V39 controller."""
import os
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
        with patch.dict(os.environ, {"AGENT_INTERFACE_CODEX_APP_SERVER_EXE": executable}):
            command = controller.app_server_command()

        self.assertEqual(command[:3], [executable, "app-server", "--stdio"])
        for feature in controller.DISABLED_FEATURES:
            self.assertIn(feature, command)
        for name in controller.DISABLED_MCPS:
            self.assertIn(f"mcp_servers.{name}.enabled=false", command)
        self.assertNotIn("mcp_servers={}", command)
        self.assertNotIn(controller.CLI, command)

    def test_legacy_node_and_cli_path_remain_the_default(self):
        with patch.dict(os.environ, {}, clear=True):
            command = controller.app_server_command()

        self.assertEqual(command[:4], [controller.NODE, controller.CLI,
                                       "app-server", "--stdio"])
        for name in controller.DISABLED_MCPS:
            self.assertIn(f"mcp_servers.{name}.enabled=false", command)


if __name__ == "__main__":
    unittest.main()
