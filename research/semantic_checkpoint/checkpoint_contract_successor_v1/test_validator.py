import unittest
from .validator import validate
class T(unittest.TestCase):
 def setUp(self): self.c={'session_id':'s','task_id':'t','checkpoint_id':2,'status':'CONFIRMED','evidence_refs':['effect:e1'],'resume_policy':'REVERIFY_REQUIRED','authority_transfer':False,'invalidated':False,'contradictory':False,'expires_at':100}
 def ok(self): return validate(self.c,session_id='s',task_id='t',last_id=1,now=10)
 def test_confirmed_is_advisory(self): self.assertEqual((self.ok().usable,self.ok().reason),(True,'advisory_progress_only')); self.assertTrue(self.ok().requires_fresh_authority)
 def test_identity_and_monotonicity(self):
  for k,v,r in (('session_id','x','session_mismatch'),('task_id','x','task_mismatch'),('checkpoint_id',1,'non_monotonic_id')):
   c=dict(self.c); c[k]=v; self.assertEqual(validate(c,session_id='s',task_id='t',last_id=1,now=10).reason,r)
 def test_safety_and_missing_controls(self):
  for k,v,r in (('status','DONE','invalid_status'),('evidence_refs',[],'missing_evidence'),('resume_policy','SKIP','missing_resume_policy'),('authority_transfer',True,'authority_transfer_forbidden'),('invalidated',True,'invalidated'),('contradictory',True,'contradictory'),('expires_at',10,'expired')):
   c=dict(self.c); c[k]=v; self.assertEqual(validate(c,session_id='s',task_id='t',last_id=1,now=10).reason,r)
 def test_unknown_and_provisional_never_gain_authority(self):
  for status in ('UNKNOWN','PROVISIONAL'):
   c=dict(self.c); c['status']=status; d=validate(c,session_id='s',task_id='t',last_id=1,now=10); self.assertTrue(d.usable); self.assertTrue(d.requires_fresh_authority)
if __name__=='__main__': unittest.main()
