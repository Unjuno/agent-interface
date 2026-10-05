import copy, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import candidate
from audit import audit
class TransformConstructionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((ROOT/'candidate_input.json').read_text())
  cls.truth=json.loads((ROOT/'oracle_truth.json').read_text())
 @classmethod
 def case(cls,name):return copy.deepcopy(next(x for x in cls.data['cases'] if x['case_id']==name))
 def test_exact_single_edge_and_composed_affine(self):
  for name in ('stable_identity','window_translation','uniform_dpi_update','mixed_monitor_update','two_epoch_composition','composed_small_uncertainty'):
   r=candidate.decide(self.case(name));self.assertEqual(r['decision'],'ADMIT',(name,r))
 def test_shared_error_cancels_only_with_same_correlation_id(self):
  r=self.case('shared_uncertainty_control');self.assertEqual(candidate.decide(r)['decision'],'ADMIT')
  r['target_correlated_uncertainty']={'different-id':[.8,.8]};self.assertEqual(candidate.decide(r)['decision'],'UNKNOWN_REFUSE')
 def test_independent_uncertainty_crossing_boundary_refuses(self):
  self.assertEqual(candidate.decide(self.case('independent_error_crosses_edge'))['decision'],'UNKNOWN_REFUSE')
 def test_invalid_epoch_units_order_duplicates_non_affine_refuse(self):
  for name in ('stale_epoch','missing_edge','reversed_edge','duplicate_edge','unit_mismatch','changed_input_dpi_context','non_affine_reflow'):
   self.assertEqual(candidate.decide(self.case(name))['decision'],'UNKNOWN_REFUSE',name)
 def test_target_identity_and_region_boundaries_fail_closed(self):
  for name in ('target_identity_swap','uncertainty_crosses_target','uncertainty_hits_forbidden'):
   self.assertEqual(candidate.decide(self.case(name))['decision'],'UNKNOWN_REFUSE',name)
 def test_oracle_rejects_wrong_mapped_point(self):
  out={'decisions':[]}
  for r in self.data['cases']:out['decisions'].append({'case_id':r['case_id'],**candidate.decide(r)})
  truth=copy.deepcopy(self.truth);truth['truth'][0]['expected_point']=[99,99]
  result=audit(self.data,out,truth);self.assertFalse(result['valid']);self.assertIn('oracle_decision_mismatch:stable_identity',result['errors'])
 def test_all_frozen_rows_meet_independent_gate(self):
  out={'decisions':[{'case_id':r['case_id'],**candidate.decide(r)} for r in self.data['cases']]}
  result=audit(self.data,out,self.truth);self.assertTrue(result['valid'],result['errors'])
if __name__=='__main__':unittest.main()
