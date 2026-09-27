import unittest
from policy import evidence_bound,pop_only,queue_only
class T(unittest.TestCase):
 def state(self,**kw):
  s=dict(interrupt_resolved=True,task_active=True,source_fresh=True,queue_version_same=True,target_identity_same=True,pending_result='NONE');s.update(kw);return s
 def test_nominal_resume(self): self.assertEqual(evidence_bound(self.state())['decision'],'RESUME')
 def test_unknown_reconcile(self): self.assertEqual(evidence_bound(self.state(pending_result='UNKNOWN'))['decision'],'RECONCILE_RESULT')
 def test_stale_yield(self): self.assertEqual(evidence_bound(self.state(source_fresh=False))['decision'],'YIELD_STALE')
 def test_queue_changed(self): self.assertEqual(evidence_bound(self.state(queue_version_same=False))['decision'],'REPLAN_QUEUE')
 def test_target_changed(self): self.assertEqual(evidence_bound(self.state(target_identity_same=False))['decision'],'REVALIDATE_TARGET')
 def test_pop_counterexample(self): self.assertEqual(pop_only(self.state(target_identity_same=False))['decision'],'RESUME')
 def test_queue_counterexample(self): self.assertEqual(queue_only(self.state(pending_result='UNKNOWN'))['decision'],'RESUME')
if __name__=='__main__': unittest.main(verbosity=2)
