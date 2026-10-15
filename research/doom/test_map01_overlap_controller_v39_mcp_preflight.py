"""Offline configuration and pre-start failure custody; never starts Codex."""
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'live_control')]
import map01_overlap_controller_v39 as controller


class MCPPreflightTests(unittest.TestCase):
    def test_invalid_or_unreadable_configuration_refuses_command(self):
        for content in ('[invalid', 'mcp_servers = ["probe"]',
                        '[mcp_servers]\nprobe = false', '[mcp_servers.""]'):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as home:
                Path(home, 'config.toml').write_text(content, encoding='utf-8')
                with patch.dict(os.environ, {'CODEX_HOME': home}), self.assertRaises(ValueError):
                    controller.app_server_command()
        with tempfile.TemporaryDirectory() as home:
            Path(home, 'config.toml').mkdir()
            with patch.dict(os.environ, {'CODEX_HOME': home}), self.assertRaises(OSError):
                controller.app_server_command()

    def test_mcp_names_are_literal_toml_keys(self):
        names = ['sample_server', 'a.b', 'quote"key', '日本語']
        with tempfile.TemporaryDirectory() as home:
            Path(home, 'config.toml').write_text('\n'.join(
                '[mcp_servers.' + json.dumps(name) + ']\ncommand = "ignored"'
                for name in names), encoding='utf-8')
            with patch.dict(os.environ, {'CODEX_HOME': home}):
                command = controller.app_server_command()
        overrides = [arg for arg in command if arg.startswith('mcp_servers.')]
        self.assertEqual(len(overrides), len(names))
        for name, override in zip(names, overrides):
            self.assertEqual(tomllib.loads(override), {'mcp_servers': {name: {'enabled': False}}})

    def run_main_failure(self, output, failure, secondary=None):
        argv = ['controller', '--out', str(output), '--model', 'offline',
                '--effort', 'low', '--measurement-session',
                '--load-fixture-manifest', 'unused.json']
        with patch.object(sys, 'argv', argv), patch.object(
                controller, 'app_server_command', side_effect=failure), patch.object(
                controller, 'CodexAppServerClient') as client:
            if secondary:
                with patch.object(Path, 'write_text', side_effect=secondary):
                    with self.assertRaises(type(failure)) as caught:
                        controller.main()
            else:
                with self.assertRaises(type(failure)) as caught:
                    controller.main()
            self.assertIs(caught.exception, failure)
            client.assert_not_called()

    def test_main_retains_bounded_failure_before_client_construction(self):
        for failure in (ValueError('SECRET configuration'), PermissionError('SECRET path')):
            with self.subTest(failure=type(failure).__name__), tempfile.TemporaryDirectory() as home:
                output = Path(home, 'out')
                self.run_main_failure(output, failure)
                raw = (output / 'mcp-preflight-failure.json').read_text(encoding='utf-8')
                receipt = json.loads(raw)
                self.assertEqual(receipt['status'], 'failed')
                self.assertEqual(receipt['stage'], 'codex_mcp_configuration_read')
                self.assertEqual(receipt['error'], {'type': type(failure).__name__,
                                                  'reason': 'configuration_unavailable'})
                self.assertNotIn('SECRET', raw)

    def test_secondary_receipt_failure_preserves_primary_exception(self):
        with tempfile.TemporaryDirectory() as home:
            failure = ValueError('SECRET primary')
            self.run_main_failure(Path(home, 'out'), failure, OSError('SECRET secondary'))
            self.assertEqual(failure.__notes__, ['MCP preflight failure receipt could not be written: OSError'])

    def test_actual_main_rejects_invalid_config_before_starting_any_client(self):
        with tempfile.TemporaryDirectory() as home:
            Path(home, 'config.toml').write_text('[invalid SECRET', encoding='utf-8')
            output = Path(home, 'out')
            argv = ['controller', '--out', str(output), '--model', 'offline',
                    '--effort', 'low', '--measurement-session',
                    '--load-fixture-manifest', 'unused.json']
            with patch.dict(os.environ, {'CODEX_HOME': home}), patch.object(
                    sys, 'argv', argv), patch.object(
                    controller, 'CodexAppServerClient') as client, patch.object(
                    controller.subprocess, 'Popen') as process:
                with self.assertRaises(tomllib.TOMLDecodeError):
                    controller.main()
                client.assert_not_called()
                process.assert_not_called()
            raw = (output / 'mcp-preflight-failure.json').read_text(encoding='utf-8')
            self.assertNotIn('SECRET', raw)
            self.assertEqual(json.loads(raw)['error']['type'], 'TOMLDecodeError')


if __name__ == '__main__':
    unittest.main()
