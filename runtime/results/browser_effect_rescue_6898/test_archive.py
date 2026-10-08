import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / 'research/live_control/reversibility_browser_effect_6695_a02_20261003_01a0ff52'


class ArchiveTests(unittest.TestCase):
    def test_manifest_and_source_freeze(self):
        lines = (PACKAGE / 'SHA256SUMS').read_bytes().splitlines()
        self.assertEqual(len(lines), 59)
        for line in lines:
            digest, name = line.decode().split(None, 1)
            self.assertEqual(hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest(), digest, name)
        freeze = json.loads((PACKAGE / 'FREEZE.json').read_bytes())
        self.assertEqual(len(freeze['source_sha256']), 10)
        for name, digest in freeze['source_sha256'].items():
            self.assertEqual(hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest(), digest)
        binding = json.loads((PACKAGE / 'SOURCE_EXECUTION_BINDING.json').read_bytes())
        self.assertEqual(binding['freeze_sha256'], hashlib.sha256((PACKAGE / 'FREEZE.json').read_bytes()).hexdigest())
        self.assertEqual((binding['candidate_launches'], binding['auditor_launches'], binding['retries']), (1, 1, 0))

    def test_entire_raw_only_audit_matches_saved_result(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'audit.json'
            result = subprocess.run([sys.executable, '-B', str(PACKAGE / 'audit.py'),
                                     str(PACKAGE / 'fixtures.json'), str(PACKAGE / 'truth.json'),
                                     str(PACKAGE / 'formal_01'), str(output)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            actual = json.loads(output.read_bytes())
        self.assertEqual(actual, json.loads((PACKAGE / 'AUDIT.json').read_bytes()))
        self.assertEqual(len(actual['rows']), 16)
        self.assertEqual(actual['counts'], {'STAGE': {'correct': 6, 'wrong': 1, 'deadline': 1},
                                          'WAIT': {'correct': 3, 'wrong': 1, 'deadline': 4}})
        outcomes = {(r['case_id'], r['policy']): r['outcome'] for r in actual['rows']}
        self.assertEqual([outcomes[('c00', p)] for p in ('STAGE', 'WAIT')], ['correct', 'deadline'])
        self.assertEqual([outcomes[('c01', p)] for p in ('STAGE', 'WAIT')], ['deadline', 'correct'])
