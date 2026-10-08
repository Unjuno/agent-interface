"""Retrospective archive checks; never launches a formal allocation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
SOURCE = PACKAGE.parent / 'counterexample_guard_refinement_6645_t0b_orbstack_20261003'


class RetainedEvidenceTests(unittest.TestCase):
    def test_original_manifest_including_recovered_logs(self):
        rows = (PACKAGE / 'SHA256SUMS.txt').read_text().splitlines()
        self.assertEqual(len(rows), 36)
        for row in rows:
            digest, relative_path = row.split('  ', 1)
            with self.subTest(path=relative_path):
                self.assertEqual(hashlib.sha256((REPO / relative_path).read_bytes()).hexdigest(), digest)

    def test_read_only_reconstruction_of_stored_audit(self):
        spec = importlib.util.spec_from_file_location('retained_6645_checker', SOURCE / 'auditor.py')
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        fixture = json.loads((SOURCE / 'fixture.json').read_text())
        raw = json.loads((PACKAGE / 'results/formal_01/candidate/raw.json').read_text())
        stored = json.loads((PACKAGE / 'results/formal_01/auditor/audit.json').read_text())
        self.assertEqual(raw['allocation_id'], 'CGREF-6645-T0C-ORB-20261003-03')
        reconstructed = checker.audit(fixture, raw)
        self.assertEqual(reconstructed, stored)
        self.assertEqual(len(raw['rows']), 10)
        self.assertEqual(stored['status'], 'PASS')
        self.assertEqual(stored['metrics']['harmful_cases'], 7)
        self.assertEqual(stored['metrics']['false_admissions']['candidate'], 0)


if __name__ == '__main__':
    unittest.main()
