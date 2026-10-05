import copy,unittest
from audit_v2 import HERE,read_case,validate
class AuditV2Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.result,cls.base,cls.bs,cls.be,cls.bsummary=read_case(HERE,'baseline')
  _,cls.candidate,cls.cs,cls.ce,cls.csummary=read_case(HERE,'candidate')
 def data(self): return copy.deepcopy((self.result,self.base,self.candidate,self.bs,self.cs,self.be,self.ce,self.bsummary,self.csummary))
 def call(self,d): return validate(HERE,*d)
 def test_retained_raw_rows_agree(self): self.assertEqual(self.call(self.data())['candidate_command'],{'op':'finish'})
 def test_baseline_error_corruption_rejected(self):
  d=list(self.data()); d[5]=d[5].replace('WinError 10093','WinError X'); self.assertRaises(AssertionError,self.call,d)
 def test_command_payload_corruption_rejected(self):
  d=self.data(); d[2]['command_events'][0]['parsed_command']={'op':'cancel'}; self.assertRaises(AssertionError,self.call,d)
 def test_thread_identity_corruption_rejected(self):
  d=self.data(); d[2]['command_events'][0]['command_thread_id']+=1; self.assertRaises(AssertionError,self.call,d)
 def test_sample_count_corruption_rejected(self):
  d=self.data(); d[8]['scheduler']['samples']-=1; self.assertRaises(AssertionError,self.call,d)
 def test_raw_stdout_truncation_rejected(self):
  d=self.data(); d[4].pop(); self.assertRaises(AssertionError,self.call,d)
if __name__=='__main__': unittest.main()
