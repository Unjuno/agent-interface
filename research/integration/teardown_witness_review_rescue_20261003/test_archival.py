"""Historical receipt checks; no source-derivation or live owner execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ARCHIVE = Path(__file__).resolve().parent.parent / 'owner_keyup_teardown_witness_5156_01a0ff58'


class ArchivalChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('archived_witness_checker', ARCHIVE / 'witness_audit.py')
        cls.checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.checker)

    def test_original_manifest_and_both_freezes(self):
        lines = (ARCHIVE / 'SHA256SUMS.txt').read_text().splitlines()
        self.assertEqual(len(lines), 54)
        for line in lines:
            expected, name = line.split(None, 1)
            self.assertEqual(hashlib.sha256((ARCHIVE / name.strip()).read_bytes()).hexdigest(), expected)
        for filename in ('FREEZE.json', 'FOLLOWUP_FREEZE.json'):
            frozen = json.loads((ARCHIVE / filename).read_text())
            for name, expected in frozen['files'].items():
                self.assertEqual(hashlib.sha256((ARCHIVE / name).read_bytes()).hexdigest(), expected)

    def test_entire_original_sixteen_row_audit_matches(self):
        result = self.checker.audit(ARCHIVE / 'review-01')
        self.assertEqual(result, json.loads((ARCHIVE / 'review-01/witness-audit.json').read_text()))
        self.assertEqual(result['rows'], 16)
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(result['contradictory_rows_accepted_by_supplement']), 15)

    def test_five_integrity_controls_on_disposable_copies(self):
        results = []
        for name in ('missing_row', 'wrong_head', 'wrong_case', 'wrong_mutation_value', 'raw_hash_corruption'):
            with tempfile.TemporaryDirectory(prefix='archival-witness-control-') as tmp:
                target = Path(tmp) / 'copied'
                shutil.copytree(ARCHIVE / 'review-01', target)
                report = json.loads((target / 'probe.json').read_bytes())
                if name == 'missing_row':
                    report['rows'].pop()
                elif name == 'wrong_head':
                    report['target_head'] = '0' * 40
                elif name == 'wrong_case':
                    report['rows'][1]['name'] = 'wrong-case'
                elif name == 'wrong_mutation_value':
                    report['rows'][1]['mutation_value'] = '0' * 32
                else:
                    raw = target / report['rows'][1]['file']
                    raw.write_bytes(raw.read_bytes() + b' ')
                (target / 'probe.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
                result = self.checker.audit(target)
                self.assertTrue(result['errors'])
                results.append({'case': name, 'errors': result['errors']})
        self.assertEqual({'positive_passed': True, 'controls': results},
                         json.loads((ARCHIVE / 'controls.json').read_text()))

    def test_saved_revision_two_record_and_type_counterexamples(self):
        result = json.loads((ARCHIVE / 'followup-v2-01/result.json').read_text())
        rows = result['retained_16_rows']
        self.assertEqual(result['retained_matrix_matches'], 16)
        self.assertEqual(len(rows), 16)
        self.assertTrue(all(row['matches'] is True for row in rows))
        self.assertEqual(rows[0]['case'], 'control')
        self.assertEqual(rows[0]['errors'], [])
        self.assertTrue(all(row['errors'] and row['independent_invalid'] for row in rows[1:]))
        self.assertEqual(result['type_boundary_false_accepts'], 2)
        variants = result['separate_type_boundary_2_rows']
        self.assertEqual(len(variants), 2)
        for row in variants:
            data = (ARCHIVE / 'followup-v2-01' / (row['case'] + '.json')).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
            self.assertEqual(row['errors'], [])
            witnesses = self.checker.gates(json.loads(data))
            self.assertTrue(witnesses)
            self.assertEqual(witnesses, row['independent_witnesses'])


if __name__ == '__main__':
    unittest.main()
