"""Read-only recovery checks, not a formal allocation rerun."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

PACKAGE = Path(__file__).resolve().parent


class ArchivalEvidenceTests(unittest.TestCase):
    def test_original_sha256_manifest(self):
        entries = (PACKAGE / 'SHA256SUMS').read_text().splitlines()
        self.assertEqual(len(entries), 19)
        for line in entries:
            digest, relative_path = line.split('  ', 1)
            with self.subTest(path=relative_path):
                self.assertEqual(hashlib.sha256((PACKAGE / relative_path).read_bytes()).hexdigest(), digest)

    def test_stored_rows_match_independent_read_only_replay(self):
        spec = importlib.util.spec_from_file_location('retained_5694_auditor', PACKAGE / 'auditor.py')
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        fixture = json.loads((PACKAGE / 'fixture.json').read_text())
        raw = json.loads((PACKAGE / 'execution/formal-01/candidate.raw.json').read_text())
        receipt = json.loads((PACKAGE / 'execution/formal-01/audit.json').read_text())
        self.assertEqual(raw['allocation_id'], fixture['allocation_id'])
        self.assertEqual(raw['rows'], checker.replay(fixture))
        self.assertEqual(len(raw['rows']), 9)
        self.assertEqual(receipt['allocation_id'], fixture['allocation_id'])
        self.assertEqual(receipt['errors'], [])
        self.assertEqual(receipt['rows_replayed'], 9)
        self.assertEqual(receipt['disposition'], 'PASS_METHOD_SCOPED')

    def test_unmatched_phase_contrast_keeps_scientific_hold(self):
        fixture = json.loads((PACKAGE / 'fixture.json').read_text())
        episodes = {row['case_id']: row for row in fixture['episodes']}
        hit, miss = episodes['phase_hit'], episodes['phase_miss']
        self.assertEqual([row['time_ms'] for row in hit['captures']], [10])
        self.assertEqual([row['time_ms'] for row in miss['captures']], [10, 50])
        self.assertEqual((hit['horizon_ms'], miss['horizon_ms']), (50, 60))
        record = json.loads((PACKAGE / 'RUN_RECORD.json').read_text())
        self.assertEqual(record['postrun_protocol_adjudication'], 'HOLD_PHASE_CONTRAST_NOT_MATCHED')
        self.assertTrue(record['no_repair_or_rerun'])


if __name__ == '__main__':
    unittest.main()
