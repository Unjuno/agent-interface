import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / 'runtime/results/receipt-pointer-01a0ff59'
SOURCE = '848b5bcce3e23ea306665761857ae6a1effc8fbe'


class ArchiveTests(unittest.TestCase):
    def test_original_manifests_and_frozen_sources(self):
        count = 0
        for folder in (PACKAGE, PACKAGE / 'peer-6874'):
            for line in (folder / 'SHA256SUMS').read_bytes().splitlines():
                digest, name = line.decode().split(None, 1)
                self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), digest)
                count += 1
        self.assertEqual(count, 24)
        freeze = json.loads((PACKAGE / 'FREEZE.json').read_bytes())
        for name, digest in freeze['hashes'].items():
            data = subprocess.check_output(['git', 'show', SOURCE + ':' + name], cwd=ROOT)
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
        baseline = json.loads((PACKAGE / 'baseline.json').read_bytes())
        self.assertEqual(hashlib.sha256((PACKAGE / 'baseline-source.py.txt').read_bytes()).hexdigest(),
                         baseline['source_sha256'])
        peer = PACKAGE / 'peer-6874'
        identity = json.loads((peer / 'FREEZE.json').read_bytes())
        self.assertEqual(hashlib.sha256((peer / 'reviewed-source.py.txt').read_bytes()).hexdigest(),
                         identity['source_sha256'])

    def test_both_raw_only_audits_match_entire_original_receipts(self):
        for folder in (PACKAGE, PACKAGE / 'peer-6874'):
            with self.subTest(folder=folder.name), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / 'audit.json'
                result = subprocess.run([sys.executable, '-B', str(folder / 'audit_boundary.py'),
                                         str(folder / 'raw.json'), str(folder / 'FREEZE.json'),
                                         str(output)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                actual = json.loads(output.read_bytes())
                self.assertEqual(actual, json.loads((folder / 'audit.json').read_bytes()))
                self.assertEqual(actual['rows'], 3333)
                self.assertEqual(actual['status'], 'PASS_FINITE_POINTER_GRAMMAR')
                self.assertEqual(len(actual['corruption_controls']), 5)
                self.assertTrue(all(c['status'] == 'FAIL_BOUNDARY' for c in actual['corruption_controls']))

    def test_original_zip_diagnostics_match_command_receipts(self):
        receipts = json.loads((PACKAGE / 'VALIDATION.json').read_bytes())
        with zipfile.ZipFile(PACKAGE / 'validation-logs.zip') as archive:
            self.assertEqual(len(archive.namelist()), 18)
            for name, receipt in receipts.items():
                for channel in ('stdout', 'stderr'):
                    data = archive.read(name + '.' + channel + '.txt')
                    self.assertEqual(hashlib.sha256(data).hexdigest(), receipt[channel + '.txt_sha256'])
        self.assertEqual(receipts['pointer-red']['exit_code'], 1)
        self.assertEqual(receipts['pointer-related']['exit_code'], 1)
        peer = PACKAGE / 'peer-6874'
        commands = json.loads((peer / 'REVIEW_CHECKS.json').read_bytes())['commands']
        with zipfile.ZipFile(peer / 'diagnostics.zip') as archive:
            self.assertEqual(len(archive.namelist()), 6)
            for receipt in commands:
                for channel in ('stdout', 'stderr'):
                    data = archive.read(receipt['name'] + '.' + channel + '.txt')
                    self.assertEqual(hashlib.sha256(data).hexdigest(), receipt[channel + '_sha256'])
