import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / 'research/analysis/soft_revisit_bias_6442_supplemental_audit_v1'


class ArchiveTests(unittest.TestCase):
    def test_manifest_and_replay_source_pins(self):
        lines = (PACKAGE / 'SHA256SUMS').read_bytes().splitlines()
        self.assertEqual(len(lines), 12)
        for line in lines:
            digest, name = line.decode().split(None, 1)
            self.assertEqual(hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest(), digest)
        binding = json.loads((PACKAGE / 'REPLAY_BINDING.json').read_bytes())
        self.assertEqual(len(binding['source_files']), 3)
        for entry in binding['source_files']:
            self.assertEqual(hashlib.sha256((PACKAGE / entry['path']).read_bytes()).hexdigest(),
                             entry['sha256'])

    def test_fresh_raw_only_replay_matches_entire_historical_receipt(self):
        binding = json.loads((PACKAGE / 'REPLAY_BINDING.json').read_bytes())
        raw = ROOT / binding['input_repository_path']
        before = raw.read_bytes()
        self.assertEqual(hashlib.sha256(before).hexdigest(), binding['input_sha256'])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'audit.json'
            result = subprocess.run([sys.executable, '-B', str(PACKAGE / 'audit_v1.py'),
                                     '--input', str(raw), '--output', str(output)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(output.read_bytes()),
                             json.loads((PACKAGE / 'supplemental-audit.json').read_bytes()))
        self.assertEqual(raw.read_bytes(), before)

    def test_publication_receipts_preserve_redaction_boundaries(self):
        entries = json.loads((PACKAGE / 'PUBLICATION_PROVENANCE.json').read_bytes())
        self.assertEqual(len(entries), 5)
        for entry in entries:
            digest = hashlib.sha256((PACKAGE / entry['file']).read_bytes()).hexdigest()
            self.assertEqual(digest, entry['published_sha256'])
            if not entry['local_path_redacted']:
                self.assertEqual(digest, entry['original_sha256'])
