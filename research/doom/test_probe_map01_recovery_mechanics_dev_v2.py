import copy, unittest
from probe_map01_recovery_mechanics_dev_v2 import direct_bounds
TOKEN='2520395d25be4e08ae711bdd07f28854'
ADM={'event':'input_admission','intent_token':TOKEN,'key':'a','admitted_ns':182584497048,'input_ack_ns':182584752580}
REL={'event':'input_release_transition','release_batch_identifier':'wait-recovery','intent_token':TOKEN,'key':'a','owner_transition_verified':True,'release_call_started_ns':182855234543,'release_call_returned_ns':182855497477}
class Tests(unittest.TestCase):
 def test_exact_dev01_sample(self):
  r=direct_bounds([ADM,REL],'wait-recovery')
  self.assertEqual(r['hold_count'],1);self.assertAlmostEqual(r['retained_lower_ms'],270.481963,6);self.assertAlmostEqual(r['retained_upper_ms'],271.000429,6)
 def test_coast_no_release_is_zero(self): self.assertEqual(direct_bounds([], 'wait-coast')['hold_count'],0)
 def test_other_program_release_ignored(self): self.assertEqual(direct_bounds([ADM,dict(REL,release_batch_identifier='other')],'wait-recovery')['hold_count'],0)
 def test_unverified_fails(self):
  with self.assertRaises(AssertionError): direct_bounds([ADM,dict(REL,owner_transition_verified=False)],'wait-recovery')
 def test_missing_admission_fails(self):
  with self.assertRaises(AssertionError): direct_bounds([REL],'wait-recovery')
 def test_duplicate_admission_fails(self):
  with self.assertRaises(AssertionError): direct_bounds([ADM,copy.deepcopy(ADM),REL],'wait-recovery')
 def test_duplicate_release_fails(self):
  with self.assertRaises(AssertionError): direct_bounds([ADM,REL,copy.deepcopy(REL)],'wait-recovery')
 def test_wrong_token_admission_fails(self):
  with self.assertRaises(AssertionError): direct_bounds([dict(ADM,intent_token='other'),REL],'wait-recovery')
 def test_bad_order_fails(self):
  with self.assertRaises(AssertionError): direct_bounds([ADM,dict(REL,release_call_started_ns=1,release_call_returned_ns=2)],'wait-recovery')
if __name__=='__main__':unittest.main()
