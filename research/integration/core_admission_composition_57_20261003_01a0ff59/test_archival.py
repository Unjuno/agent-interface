"""Read-only archive checks; do not execute a runtime or original producer."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

import audit_matrix

ROOT = Path(__file__).resolve().parent


class ArchivalChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = audit_matrix.read_gzip(ROOT / 'raw/cases.jsonl.gz')
        cls.rows = audit_matrix.read_gzip(ROOT / 'raw/results.jsonl.gz')

    def test_original_manifest_freeze_and_raw_binding(self):
        lines = (ROOT / 'SHA256SUMS').read_text().splitlines()
        self.assertEqual(len(lines), 42)
        for line in lines:
            expected, name = line.split(None, 1)
            self.assertEqual(hashlib.sha256((ROOT / name.strip()).read_bytes()).hexdigest(), expected)
        frozen = json.loads((ROOT / 'FREEZE.json').read_text())
        self.assertEqual(len(frozen['source_sha256']), 12)
        for name, expected in frozen['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)
        receipt = json.loads((ROOT / 'raw/RECEIPT.json').read_text())
        for name, expected in receipt['raw_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / 'raw' / name).read_bytes()).hexdigest(), expected)

    def test_saved_audit_matches_entire_original_result(self):
        result = audit_matrix.verify(self.cases, self.rows)
        self.assertEqual(result, json.loads((ROOT / 'AUDIT.json').read_text()))
        self.assertEqual(result['rows'], 36000)
        self.assertEqual(result['cases_per_arm'], 9000)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['mismatches'], {'main': 1654, 'enum': 904, 'scalar': 750, 'combined': 0})

    def test_six_in_memory_raw_corruptions_are_rejected(self):
        for mutation in ('missing_row', 'duplicate_row', 'wrong_input_hash',
                         'bool_to_integer', 'case_type_change', 'input_mutation'):
            cases, rows = self.cases, self.rows
            if mutation == 'missing_row':
                rows = rows[:-1]
            elif mutation == 'duplicate_row':
                rows = rows + [rows[0]]
            elif mutation == 'case_type_change':
                cases = deepcopy(cases)
                cases[0]['evidence']['current_observation_seq'] = 1.0
            else:
                rows = deepcopy(rows)
                row = next(r for r in rows if r['arm'] == 'combined')
                if mutation == 'wrong_input_hash':
                    row['input_sha256'] = '0' * 64
                elif mutation == 'bool_to_integer':
                    row['output']['accepted'] = int(row['output']['accepted'])
                else:
                    row['unchanged'] = False
            with self.subTest(mutation=mutation):
                self.assertTrue(audit_matrix.verify(cases, rows)['errors'])

    def test_historical_control_receipt_is_preserved_not_reexecuted(self):
        result = json.loads((ROOT / 'CONTROLS.json').read_text())
        self.assertEqual((result['raw_controls'], result['source_controls']), (6, 4))
        self.assertTrue(result['all_detected'])
        self.assertEqual(len(result['details']), 10)
        self.assertTrue(all(row['detected'] is True for row in result['details']))


if __name__ == '__main__':
    unittest.main()
