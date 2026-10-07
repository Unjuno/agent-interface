import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / 'research/integration/motor_context_2530_20261003_45e9'


class RecoveryTests(unittest.TestCase):
    def test_all_original_packet_hashes(self):
        lines = (PACKAGE / 'SHA256SUMS').read_bytes().splitlines()
        self.assertEqual(len(lines), 52)
        for line in lines:
            digest, name = line.decode().split(None, 1)
            self.assertEqual(hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest(), digest, name)

    def test_both_saved_raw_only_audits(self):
        for stage, mode in (('before', 'before'), ('after', 'after')):
            with tempfile.TemporaryDirectory() as directory:
                raw = Path(directory) / (stage + '.jsonl')
                for suffix in ('.jsonl', '.summary.json'):
                    shutil.copyfile(PACKAGE / 'observed' / (stage + suffix), raw.with_suffix(suffix))
                result = subprocess.run([sys.executable, '-B', str(PACKAGE / 'tools/audit.py.txt'),
                                         str(PACKAGE / 'cases.jsonl'), str(raw),
                                         str(PACKAGE / 'CORPUS_FREEZE.json'), mode], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(json.loads(raw.with_suffix('.audit.json').read_bytes()),
                                 json.loads((PACKAGE / 'observed' / (stage + '.audit.json')).read_bytes()))

    def test_current_tree_finite_api_corpus_matches_repaired_result(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory) / 'current.jsonl'
            result = subprocess.run([sys.executable, '-B', str(PACKAGE / 'tools/candidate.py.txt'),
                                     str(ROOT), str(PACKAGE / 'cases.jsonl'), str(raw)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(raw.read_bytes(), (PACKAGE / 'observed/after.jsonl').read_bytes())
            self.assertEqual(json.loads(raw.with_suffix('.summary.json').read_bytes()),
                             json.loads((PACKAGE / 'observed/after.summary.json').read_bytes()))
