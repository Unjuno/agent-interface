"""Corrupted boundary traces must fail the independent oracle."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

PACKAGE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location('sequence_raw_audit', PACKAGE / 'audit.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RawAuditTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads((PACKAGE / 'after.json').read_text(encoding='utf-8'))

    def test_unchanged_after_passes_and_original_before_remains_failed(self):
        self.assertEqual(MODULE.audit(self.raw)['errors'], [])
        before = json.loads((PACKAGE / 'before.json').read_text(encoding='utf-8'))
        self.assertEqual(len(MODULE.audit(before)['errors']), 11)

    def test_missing_or_duplicated_row_cannot_reduce_denominator(self):
        for duplicate in (False, True):
            raw = copy.deepcopy(self.raw)
            raw['rows'].pop()
            if duplicate:
                raw['rows'].append(copy.deepcopy(raw['rows'][0]))
            self.assertIn('coverage', MODULE.audit(raw)['errors'])

    def test_dispatched_malformed_sequence_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        row = next(r for r in raw['rows'] if r['case_id'] == '1:true:valid')
        row['calls']['execute'] = 1
        row['dispatched'] = [{'type': 'bool', 'repr': 'True'}]
        self.assertIn('1:true:valid:boundary', MODULE.audit(raw)['errors'])

    def test_lost_valid_integer_action_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        row = next(r for r in raw['rows'] if r['case_id'] == '7:equal_int:valid')
        row['calls']['execute'] = 0
        row['dispatched'] = []
        self.assertIn('7:equal_int:valid:boundary', MODULE.audit(raw)['errors'])

    def test_scope_relabel_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw['rows'][0]['observation_sequence'] = 1
        self.assertIn('0:equal_int:valid:identity', MODULE.audit(raw)['errors'])


if __name__ == '__main__':
    unittest.main()
