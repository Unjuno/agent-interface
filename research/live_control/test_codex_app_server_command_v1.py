import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research.live_control.codex_app_server_command_v1 import command


class AppServerCommandMcpIsolationTests(unittest.TestCase):
    def test_disables_only_servers_present_in_codex_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home / 'config.toml').write_text(
                '[mcp_servers.node_repl]\ncommand = "node"\n'
                '[mcp_servers.openaiDeveloperDocs]\nurl = "https://example.invalid/mcp"\n',
                encoding='utf-8')
            with patch.dict(os.environ, {'CODEX_HOME': str(home)}):
                result = command('node', 'cli.js')
        overrides = [result[index + 1] for index, value in enumerate(result[:-1])
                     if value == '-c' and result[index + 1].startswith('mcp_servers.')]
        self.assertEqual(overrides, [
            'mcp_servers.node_repl.enabled=false',
            'mcp_servers.openaiDeveloperDocs.enabled=false',
        ])
        self.assertNotIn('mcp_servers.blender.enabled=false', result)
        self.assertNotIn('mcp_servers.chrome-devtools.enabled=false', result)

    def test_quotes_non_bare_mcp_names_in_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home / 'config.toml').write_text(
                '[mcp_servers.\"private.mcp\"]\ncommand = \"node\"\n',
                encoding='utf-8')
            result = command('node', 'cli.js', codex_home=home)
        self.assertIn('mcp_servers.\"private.mcp\".enabled=false', result)

    def test_missing_config_adds_no_unknown_mcp_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.dict(os.environ, {'CODEX_HOME': str(Path(temporary) / 'empty')}):
                result = command('node', 'cli.js')
        self.assertFalse(any(value.startswith('mcp_servers.') for value in result))


if __name__ == '__main__':
    unittest.main()