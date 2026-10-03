"""Ordinary cause-consistency regressions on retained JSON, no kernel import."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'audit_reasons_v2.py'
spec = importlib.util.spec_from_file_location('retained_reason_oracle', SOURCE)
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)
RAW = json.loads((ROOT.parent/'matrix.raw.json').read_bytes())

class CapturedCauseTests(unittest.TestCase):
    def refused_reason(self, index, reason):
        record = copy.deepcopy(RAW)
        self.assertNotEqual(record['rows'][index]['error_message'], reason)
        record['rows'][index]['error_message'] = reason
        result = oracle.audit(record)
        self.assertEqual(result['errors'], [f'{index}:error_message'])
        self.assertEqual(result['decision'], 'HOLD_ORDER_EVIDENCE')
    def test_original_complete_positive(self):
        result = oracle.audit(RAW)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['accepted'], {'baseline':16,'observation_floor':12,'authorization_floor':5})
        self.assertEqual(result['before_grant_accepted'], {'baseline':11,'observation_floor':7,'authorization_floor':0})
    def test_exact_first_reviewer_copy(self):
        self.refused_reason(1, 'authority expired before execution')
    def test_exact_second_reviewer_copy(self):
        self.refused_reason(100, 'execution request changed bound target or authority')
    def test_observation_floor_precedes_mismatch(self):
        self.refused_reason(37, 'execution request changed bound target or authority')
    def test_expiry_precedes_mismatch(self):
        self.refused_reason(17, 'execution request changed bound target or authority')
    def test_authorization_floor_precedes_mismatch(self):
        self.refused_reason(73, 'execution request changed bound target or authority')
    def test_invented_nonempty_refusal_text(self):
        self.refused_reason(1, 'source-impossible synthetic refusal')
    def test_accepted_message_must_remain_null(self):
        record = copy.deepcopy(RAW)
        self.assertIs(record['rows'][0]['accepted'], True)
        record['rows'][0]['error_message'] = 'execution request changed bound target or authority'
        result = oracle.audit(record)
        self.assertEqual(result['errors'], ['0:accepted_evidence'])

if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]], verbosity=2)
