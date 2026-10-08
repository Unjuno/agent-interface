import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / 'runtime/results/admission-context-01a0ff2d'


class ArchiveTests(unittest.TestCase):
    def test_manifests_and_original_source_aliases(self):
        supplemental = json.loads((PACKAGE / 'PUBLIC_MANIFEST_REPLICATION_V2.json').read_bytes())
        original = json.loads((PACKAGE / 'PUBLIC_MANIFEST.json').read_bytes())
        aliases = supplemental['original_source_aliases']
        for manifest in (original, supplemental):
            for name, digest in manifest['sha256'].items():
                target = ROOT / aliases.get(name, name)
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), digest, name)
        self.assertEqual(supplemental['single_runtime_delivery_pr'], 6866)

    def test_raw_only_audit_matches_entire_retained_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / 'audit.json'
            result = subprocess.run([sys.executable, '-B', str(PACKAGE / 'audit_replication_v2.py'),
                                     str(receipt)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            actual = json.loads(receipt.read_bytes())
        self.assertEqual(actual, json.loads((PACKAGE / 'audit-replication-v2.json').read_bytes()))
        self.assertEqual(actual['rows'], 44)
        self.assertEqual(actual['baseline_decision_gaps'], 30)
        self.assertEqual(actual['baseline_unexpected_exceptions'], 4)
        self.assertEqual(len(actual['corruption_controls']), 9)
        self.assertTrue(all(item['rejected'] for item in actual['corruption_controls']))
        self.assertIs(actual['external_non_author_review'], False)

    def test_publication_redaction_is_not_lost_original_evidence(self):
        entries = json.loads((PACKAGE / 'LOG_PUBLICATION.json').read_bytes())
        for entry in entries:
            digest = hashlib.sha256((PACKAGE / entry['path']).read_bytes()).hexdigest()
            self.assertEqual(digest, entry['public_sha256'])
            if not entry['redacted']:
                self.assertEqual(digest, entry['original_sha256'])
        self.assertEqual([entry['path'] for entry in entries if entry['redacted']],
                         ['before-tests.txt'])
