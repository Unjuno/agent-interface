import unittest
from policy import authority_guarded,handoff_fenced

class T(unittest.TestCase):
 def lease(self,**kw):
  d={'authority_id':'T1','resource':'locomotion','generation':1,'active':True,'valid_context':True,'start_tick':0,'end_tick':20};d.update(kw);return d
 def p(self,pid,source,gen,at=11,resource='locomotion',authority_id=None):
  return {'proposal_id':pid,'resource':resource,'source':source,'generation':gen,'authority_id':authority_id,'proposed_at':at,'ready':True}
 def test_baseline_releases_old_deopt_after_expiry(self):
  o=authority_guarded([self.p('d','deopt',1)],[self.lease()],{'locomotion':2},21);self.assertEqual(o['selected']['locomotion']['source'],'deopt')
 def test_candidate_rejects_old_deopt_after_expiry(self):
  o=handoff_fenced([self.p('d','deopt',1)],[self.lease()],{'locomotion':2},21);self.assertNotIn('locomotion',o['selected'])
 def test_candidate_allows_fresh_deopt_after_expiry(self):
  o=handoff_fenced([self.p('d2','deopt',2,21)],[self.lease()],{'locomotion':2},21);self.assertEqual(o['selected']['locomotion']['source'],'deopt')
 def test_candidate_rejects_expired_threat_even_current_generation(self):
  o=handoff_fenced([self.p('t','threat',2,21,authority_id='T1')],[self.lease()],{'locomotion':2},21);self.assertNotIn('locomotion',o['selected'])
 def test_candidate_rejects_invalidated_old_deopt(self):
  l=self.lease(valid_context=False);o=handoff_fenced([self.p('d','deopt',1)],[l],{'locomotion':2},12);self.assertNotIn('locomotion',o['selected'])
 def test_no_authority_liveness(self):
  o=handoff_fenced([self.p('d','deopt',1)],[],{'locomotion':1},12);self.assertEqual(o['selected']['locomotion']['source'],'deopt')
 def test_nonoverlap(self):
  fire=self.lease(resource='fire');t=self.p('t','threat',1,10,'fire','T1');d=self.p('d','deopt',1,11,'locomotion');o=handoff_fenced([t,d],[fire],{'fire':1,'locomotion':1},12);self.assertEqual(set(o['selected']),{'fire','locomotion'})
 def test_active_overlap_preserved(self):
  t=self.p('t','threat',1,10,authority_id='T1');d=self.p('d','deopt',1,11);o=handoff_fenced([t,d],[self.lease()],{'locomotion':1},12);self.assertEqual(o['selected']['locomotion']['source'],'threat')
if __name__=='__main__':unittest.main()
