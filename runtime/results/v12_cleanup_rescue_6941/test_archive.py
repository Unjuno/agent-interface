"""Retained custody and finite endpoint checks; no game or producer execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'research/doom/session_cleanup_save_refusal_59_20261003_01a0ff58'
PACKET = ROOT / REL
SOURCE = 'c7d6f4cf2f716373065dac90a725fd8275896563'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(name):
    return json.loads((PACKET / name).read_bytes())

class ArchiveTests(unittest.TestCase):
    def test_complete_original_git_manifest_custody_and_source_exports(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', REL], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths), 173)
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes(), subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT))
        manifest = load('MANIFEST.json')['files']
        self.assertEqual(set(manifest), {p[len(REL) + 1:] for p in paths} - {'MANIFEST.json'})
        for name, item in manifest.items():
            data = (PACKET / name).read_bytes()
            self.assertEqual((len(data), sha(data)), (item['bytes'], item['sha256']))
        for item in load('CUSTODY.json')['files']:
            data = (PACKET / item['public_path']).read_bytes()
            self.assertEqual((len(data), sha(data)), (item['public_bytes'], item['public_sha256']))
        exports = load('records/SOURCE-EXPORT.json')
        self.assertEqual(len(exports['files']), 21)
        for path, item in exports['files'].items():
            data = (PACKET / 'records/original-source' / (path + '.txt')).read_bytes()
            self.assertEqual((len(data), sha(data)), (item['bytes'], item['sha256']))
            self.assertEqual(data, subprocess.check_output(['git', 'show', exports['base'] + ':' + path], cwd=ROOT))

    def test_six_retained_main_endpoints_and_four_unit_first_outcomes(self):
        for phase, repaired in [('first-original-01', False), ('repaired-main-01', True), ('repaired-main-02-config-preservation', True)]:
            for index, kind in enumerate(['normal', 'owner-file-refusal']):
                prefix = 'records/' + phase + '/' + str(index).zfill(2) + '-' + kind
                result = load(prefix + '/FINAL-RECEIPT.json')
                before = load(prefix + '/AT-MAIN-RETURN.json')
                self.assertTrue(all(result[key] == value for key, value in before.items()))
                bad_original = kind == 'owner-file-refusal' and not repaired
                self.assertEqual(result['input_lines'], 0)
                self.assertEqual(result['actual_executor'], 'executor_v12')
                self.assertEqual(result['backend_close_at_main_return'], 1)
                self.assertEqual(result['session_close_at_main_return'], 0 if bad_original else 1)
                self.assertEqual(result['game_close_at_main_return'], 0 if bad_original else 1)
                if bad_original:
                    self.assertIsNone(result['child_exit_at_main_return'])
                else:
                    self.assertEqual(result['child_exit_at_main_return'], 0)
                self.assertEqual(result['owned_child_final_exit'], 0)
                terminal = (PACKET / prefix / 'owned-child-terminal.bin').read_bytes()
                self.assertIn(terminal, [b'PRIVATE-INERT-EOF\n', b'PRIVATE-INERT-EOF\r\n'])
                self.assertEqual(result['owned_child_terminal'], terminal.decode('ascii'))
                if kind == 'owner-file-refusal':
                    self.assertIs(result['main_error']['is_os_error'], True)
                    self.assertEqual(result['main_error']['type'], 'PermissionError')
                else:
                    self.assertIsNone(result['main_error'])
        for phase, exit_code in [('first-unit-red-01', 1), ('first-unit-red-02-fixture-repair', 1), ('first-unit-green-01', 0), ('unit-green-02-config-preservation', 0)]:
            prefix = 'records/' + phase
            receipt = load(prefix + '/RECEIPT.json')
            self.assertEqual(receipt['exit_code'], exit_code)
            self.assertIn(b'Ran 9 tests', (PACKET / prefix / 'stderr.bin').read_bytes())

if __name__ == '__main__':
    unittest.main()
