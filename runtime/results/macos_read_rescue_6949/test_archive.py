"""Exact saved Mac experiment custody; never replay native I/O."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKET = 'research/concurrency/macos_read_cancel_6501_20261003_01a0ff52_93c2'
BASE = ROOT / PACKET
SOURCE = '8585aa538a19e6472b5a476638ddb1f755b24f91'


def read(path):
    return json.loads((BASE / path).read_bytes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Custody(unittest.TestCase):
    def test_original_files_and_public_projection_joins(self):
        files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE, '--', PACKET], cwd=ROOT).decode().splitlines()
        self.assertEqual(len(files), 61)
        for path in files:
            self.assertEqual((ROOT / path).read_bytes(), subprocess.check_output(['git', 'show', f'{SOURCE}:{path}'], cwd=ROOT))
        manifest = read('MANIFEST.json')['files']
        self.assertEqual(len(manifest), 60)
        for path, pin in manifest.items():
            data = (BASE / path).read_bytes()
            self.assertEqual(len(data), pin['bytes'])
            self.assertEqual(digest(data), pin['sha256'])
        for join in read('PUBLICATION.json')['joins']:
            data = (BASE / join['public_relative_path']).read_bytes()
            self.assertEqual(len(data), join['public_bytes'])
            self.assertEqual(digest(data), join['public_sha256'])
            if join['transform'] == 'exact':
                self.assertEqual(digest(data), join['original_sha256'])

    def test_saved_roster_and_literal_sequence(self):
        raw = read('first-result/raw/raw.json')
        self.assertEqual(raw['schema'], 'macos-owned-read-completion-v1')
        self.assertEqual(len(raw['cases']), 8)
        self.assertEqual(sum(len(c['events']) for c in raw['cases']), 114)
        roster = []
        for case in raw['cases']:
            events = case['events']
            self.assertEqual([e['seq'] for e in events], list(range(len(events))))
            self.assertEqual(events[0]['name'], 'case_begin')
            roster.append((events[0]['data']['mode'], events[0]['data']['rep']))
        self.assertEqual(sorted(roster), sorted((mode, rep) for mode in ['wrapper_cancel', 'caller_close', 'owned_control', 'normal_data'] for rep in [0, 1]))


if __name__ == '__main__':
    unittest.main()
