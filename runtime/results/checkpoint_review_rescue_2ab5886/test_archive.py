"""Retained independent interval oracle; no producer or historical writer."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
REL = 'research/reviews/checkpoint_delivery_6918_45e9'
PACKET = ROOT / REL
PRIMARY = ROOT / 'research/analysis/checkpoint_delivery_6089_20261003_01a0ff59'
SOURCE = '2ab5886b8ca535e299296671cf30be832752f9e3'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(name):
    return json.loads((PACKET / name).read_bytes())

class ArchiveTests(unittest.TestCase):
    def test_original_git_manifest_and_public_derivatives(self):
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', REL], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths), 24)
        for path in paths:
            self.assertEqual((ROOT / path).read_bytes(), subprocess.check_output(['git', 'show', SOURCE + ':' + path], cwd=ROOT))
        manifest = {}
        for line in (PACKET / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertNotIn(name, manifest)
            manifest[name] = digest
            self.assertEqual(sha((PACKET / name).read_bytes()), digest)
        self.assertEqual(set(manifest), {p[len(REL) + 1:] for p in paths} - {'SHA256SUMS'})
        for item in load('PROVENANCE.json')['artifacts']:
            self.assertEqual(sha((PACKET / item['artifact']).read_bytes()), item['public_sha256'])

    def test_complete_independent_interval_oracle_and_twelve_controls(self):
        tree = ast.parse((PACKET / 'tools/independent.py.txt').read_bytes())
        nodes = [node for node in tree.body if not isinstance(node, ast.If) and not
                 (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in {'ROOT', 'PACKAGE'} for target in node.targets))]
        namespace = {'PACKAGE': PRIMARY, '__file__': str(PACKET / 'tools/independent.py.txt')}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), '<retained-interval-oracle>', 'exec'), namespace)
        raw = json.loads((PRIMARY / 'raw.json').read_bytes())
        actual = namespace['validate'](raw)
        recorded = load('checks/INDEPENDENT_RESULT.json')
        self.assertEqual(actual, {key: recorded[key] for key in actual})
        controls = namespace['controls'](raw)
        self.assertEqual(controls, recorded['new_copied_raw_controls'])
        self.assertEqual(len(controls), 12)
        self.assertTrue(all(row['rejected'] for row in controls))
        self.assertEqual(actual['rows'], 24)
        self.assertEqual(len(actual['legacy_empty_contract_mismatches']), 3)
        self.assertEqual(actual['normalized_mismatches'], 0)
        for duration, expected in [(6, {'safe': True, 'first_unsafe_step': None, 'worst_position': 12}),
                                   (7, {'safe': False, 'first_unsafe_step': 7, 'worst_position': 14})]:
            self.assertEqual(namespace['envelope'](14, duration), expected)

if __name__ == '__main__':
    unittest.main()
