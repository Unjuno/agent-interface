import unittest
from policy import classify
BASE=dict(request_id='r',target_present=True,authority_current=True,capability_supported=True,constraints_satisfiable=True,modal_blocking=False,input_dispatched=False,app_request_seen=False,pending_receipt=False,effect_receipts=[],evidence_complete=True,deadline_elapsed=False)
class T(unittest.TestCase):
 def lab(self,**kw):
  e=BASE.copy(); e.update(kw); return classify(e)['label']
 def test_success(self): self.assertEqual(self.lab(effect_receipts=[{'request_id':'r','value':'DONE'}]),'SUCCEEDED')
 def test_unknown(self): self.assertEqual(self.lab(evidence_complete=False),'FAILED_UNKNOWN')
 def test_impossible(self): self.assertEqual(self.lab(constraints_satisfiable=False),'IMPOSSIBLE_UNDER_CONSTRAINTS')
 def test_cap(self): self.assertEqual(self.lab(capability_supported=False),'CAPABILITY_UNSUPPORTED')
 def test_target(self): self.assertEqual(self.lab(target_present=False),'TARGET_NOT_FOUND')
 def test_auth(self): self.assertEqual(self.lab(authority_current=False),'AUTHORITY_REQUIRED')
 def test_blocked(self): self.assertEqual(self.lab(modal_blocking=True),'BLOCKED')
 def test_progress(self): self.assertEqual(self.lab(input_dispatched=True,app_request_seen=True,pending_receipt=True),'IN_PROGRESS')
 def test_conflict(self): self.assertEqual(self.lab(effect_receipts=[{'request_id':'r','value':'DONE'},{'request_id':'r','value':'NOT_DONE'}]),'CONFLICT')
if __name__=='__main__': unittest.main()
