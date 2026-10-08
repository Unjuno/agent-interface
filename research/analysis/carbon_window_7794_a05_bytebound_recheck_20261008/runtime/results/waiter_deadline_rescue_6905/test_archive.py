import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / 'research/concurrency/singleflight_waiter_deadline_6501_01a0ff2d'


class ArchiveTests(unittest.TestCase):
    def test_all_public_manifest_hashes(self):
        entries = json.loads((PACKAGE / 'PUBLIC_MANIFEST.json').read_bytes())['sha256']
        self.assertEqual(len(entries), 26)
        for name, digest in entries.items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest, name)

    def test_complete_raw_only_audit_matches_historical_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'audit.json'
            result = subprocess.run([sys.executable, '-B', str(PACKAGE / 'audit.py'),
                                     str(PACKAGE / 'raw.json'), str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            actual = json.loads(output.read_bytes())
        self.assertEqual(actual, json.loads((PACKAGE / 'audit.json').read_bytes()))
        self.assertEqual(actual['rows'], 30)
        self.assertEqual(actual['waiter_outcomes'], 60)
        self.assertEqual(len(actual['corruption_controls']), 8)
        self.assertTrue(all(c['rejected'] for c in actual['corruption_controls']))
        self.assertEqual(actual['summary'], {
            'direct': {'rows': 10, 'late_admissions': 4, 'companion_cancelled': 2},
            'shield': {'rows': 10, 'late_admissions': 2, 'companion_cancelled': 0},
            'shield_deadline': {'rows': 10, 'late_admissions': 0, 'companion_cancelled': 0}})
