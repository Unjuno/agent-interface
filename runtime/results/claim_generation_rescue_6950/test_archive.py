"""Independent saved four-case table; no archived producer or writer imports."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKET = 'research/analysis/claim_generation_types_6509_01a0ff58'
BASE = ROOT / PACKET
SOURCE = 'e0bb8131cdbde3f0369320514eb8a211bed122da'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads((BASE / path).read_bytes())


class SavedBoundary(unittest.TestCase):
    def test_exact_custody(self):
        files = git('ls-tree', '-r', '--name-only', SOURCE, '--', PACKET).decode().splitlines()
        self.assertEqual(len(files), 34)
        for path in files:
            self.assertEqual((ROOT / path).read_bytes(), git('show', f'{SOURCE}:{path}'))
        sums = (BASE / 'SHA256SUMS').read_text().splitlines()
        self.assertEqual(len(sums), 33)
        for line in sums:
            digest, path = line.split(maxsplit=1)
            self.assertEqual(sha((BASE / path).read_bytes()), digest)
        for pin in read('SOURCE_PINS.json'):
            data = git('show', f"{pin['git_commit']}:{pin['git_path']}")
            self.assertEqual(data, (BASE / pin['published_copy']).read_bytes())
            self.assertEqual(len(data), pin['bytes'])
            self.assertEqual(sha(data), pin['sha256'])
        freeze = read('FREEZE.json')
        for path, expected in freeze['source_input_sha256'].items():
            self.assertEqual(sha((BASE / path).read_bytes()), expected)

    def test_complete_typed_saved_table(self):
        raw = read('results/raw.json')
        freeze = read('FREEZE.json')
        self.assertEqual(raw['run_id'], freeze['run_id'])
        self.assertLess(datetime.fromisoformat(freeze['frozen_utc']), datetime.fromisoformat(raw['started_utc']))
        self.assertLess(datetime.fromisoformat(raw['started_utc']), datetime.fromisoformat(raw['finished_utc']))
        self.assertIs(type(raw['pid']), int)
        self.assertGreater(raw['pid'], 0)
        for phase in ['before', 'after']:
            self.assertEqual(raw['source_input_sha256_' + phase], freeze['source_input_sha256'])
        checks = ['identity', 'freshness', 'effect']
        complete = dict(disposition='COMPLETE_VERDICT', reason='MANDATORY_COMPLETE', completed=checks, missing=[])
        stale = dict(disposition='PARTIAL_UNKNOWN', reason='GENERATION_OR_SCOPE', completed=[], missing=checks)
        invalid = dict(disposition='PARTIAL_UNKNOWN', reason='REQUEST_GENERATION_TYPE', completed=[], missing=checks)
        table = [('int-current', int, 1, complete, complete), ('int-stale', int, 2, stale, stale),
                 ('bool-alias', bool, True, complete, invalid), ('float-alias', float, 1.0, complete, invalid)]
        self.assertEqual(len(raw['rows']), 4)
        self.assertEqual(len(raw['request_cases']), 4)
        for row, declared, expected in zip(raw['rows'], raw['request_cases'], table):
            name, kind, value, legacy, strict = expected
            self.assertIs(type(row['generation_value']), kind)
            self.assertIs(type(declared['value']), kind)
            self.assertEqual(row, dict(id=name, generation_type=kind.__name__, generation_value=value, legacy=legacy, strict=strict))
            self.assertEqual(declared, dict(id=name, python_type=kind.__name__, value=value))
        saved = read('results/AUDIT.json')
        self.assertEqual(saved['raw_sha256'], sha((BASE / 'results/raw.json').read_bytes()))
        self.assertEqual(len(saved['controls']), 5)
        self.assertTrue(all(c['effective'] is True and c['rejected'] is True and c['errors'] for c in saved['controls']))


if __name__ == '__main__':
    unittest.main()
