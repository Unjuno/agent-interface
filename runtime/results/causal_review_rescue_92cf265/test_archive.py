"""Immutable custody and deterministic copied-row joins, not a native replay."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = '92cf265b15613b907b23504a53e4c487be0cad3e'
HEAD = '5516baf54c92a120d651c08f4163707549678b04'
PACKET = 'research/reviews/scorer_native_causal_6928_20261003_01a0ff52_5884'
DATA = 'research/doom/scorer_native_input_effect_59_20261003_b64b/formal_01/candidate/result'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def pin(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def read(name):
    return json.loads((ROOT / PACKET / name).read_bytes())


class Archive(unittest.TestCase):
    def test_exact_archive(self):
        files = git('ls-tree', '-r', '--name-only', SOURCE, '--', PACKET).decode().splitlines()
        self.assertEqual(len(files), 32)
        for path in files:
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_bytes(), git('show', f'{SOURCE}:{path}'))
        manifest = read('MANIFEST.json')
        self.assertEqual(len(manifest), 31)
        for path, expected in manifest.items():
            self.assertEqual(pin((ROOT / PACKET / path).read_bytes()), expected)

    def test_twelve_copied_control_joins(self):
        report = read('copied-control-comparison.json')
        raw_bytes = git('show', f'{HEAD}:{DATA}/RAW.json')
        self.assertEqual(hashlib.sha256(raw_bytes).hexdigest(), report['original_raw_sha256'])
        self.assertEqual(report['head'], HEAD)
        self.assertEqual(report['original_rows_pass'], 16)
        self.assertEqual(report['original_author_v2_errors'], [])
        controls = report['controls']
        self.assertEqual(len(controls), 12)
        self.assertEqual(sum(c['author_v2_accepts'] is True for c in controls), 7)
        for control in controls:
            with self.subTest(control=control['name']):
                base = ROOT / PACKET / 'controls' / control['name']
                changed = json.loads((base / 'changed-row.json').read_bytes())
                self.assertEqual(changed['case']['id'], control['cell'])
                raw = json.loads(raw_bytes)
                index = next(i for i, row in enumerate(raw['rows']) if row['case']['id'] == control['cell'])
                raw['rows'][index] = changed
                serialized = (json.dumps(raw, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
                self.assertEqual(pin(serialized), control['mutated_raw'])
                self.assertEqual(changed['artifacts'], control['honestly_rejoined_artifacts'])
                for path, expected in changed['artifacts'].items():
                    saved = base / 'changed-artifacts' / path
                    data = saved.read_bytes() if saved.exists() else git('show', f'{HEAD}:{DATA}/{path}')
                    self.assertEqual(pin(data), expected)
                self.assertTrue(control['independent_rejection'])
                self.assertEqual(control['author_v2_accepts'], not control['author_v2_errors'])
        original = read('independent-original-result.json')
        self.assertEqual(original['rows'], 16)
        for key, value in [('samples', 286), ('reads', 66), ('effects', 12)]:
            self.assertEqual(sum(row[key] for row in original['outcomes']), value)
            self.assertEqual(original[key], value)


if __name__ == '__main__':
    unittest.main()
