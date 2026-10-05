"""Mutation controls for the raw-only post-batch sample auditor."""
import copy,importlib.util,json
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('postbatch_audit',HERE/'audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
RAW=json.loads((HERE/'results/a02/raw.json').read_text())
class AuditControls(unittest.TestCase):
 def test_retained_three_scenario_result_audits(self):
  self.assertEqual([audit.check_case(x)['scenario'] for x in RAW['scenarios']],['normal','release_stuck','sample_error'])
 def test_inter_release_query_is_rejected(self):
  case=copy.deepcopy(RAW['scenarios'][0]); ups=[x for x in case['operations'] if x['event']=='key_up']
  case['operations'].append({'event':'query_keymap','time_ns':(ups[0]['time_ns']+ups[1]['time_ns'])//2})
  with self.assertRaises(AssertionError): audit.check_case(case)
 def test_keycode_mismatch_is_rejected(self):
  case=copy.deepcopy(RAW['scenarios'][0]); case['events'][-2]['post_batch_key_state_sample']['keycode']=999
  with self.assertRaises(AssertionError): audit.check_case(case)
 def test_missing_sample_is_rejected(self):
  case=copy.deepcopy(RAW['scenarios'][0]); case['events'][-2].pop('post_batch_key_state_sample')
  with self.assertRaises(AssertionError): audit.check_case(case)
 def test_owner_identity_mismatch_is_rejected(self):
  case=copy.deepcopy(RAW['scenarios'][0]); case['events'][-2]['post_batch_key_state_sample']['intent_token']='other'
  with self.assertRaises(AssertionError): audit.check_case(case)
if __name__=='__main__': unittest.main(verbosity=2)
