import unittest
import study
class T(unittest.TestCase):
 def test_trace_count(self): self.assertEqual(len(study.trace()),13)
 def test_unrelated_same_semantics(self):
  a,b=study.trace()[:2]
  self.assertEqual({p:study.evaluate(p,a) for p in study.PREDICATES},{p:study.evaluate(p,b) for p in study.PREDICATES})
 def test_form_flip(self):
  s=study.trace()[2];self.assertEqual(study.evaluate('FORM_COMPLETE',s),'FALSE')
 def test_unknown(self):
  s=study.trace()[6];self.assertEqual(study.evaluate('MODAL_BLOCKING',s),'UNKNOWN')
 def test_stale_all_unknown(self):
  s=study.trace()[7];self.assertTrue(all(study.evaluate(p,s)=='UNKNOWN' for p in study.PREDICATES))
 def test_run_semantics(self):
  r=study.run();self.assertTrue(all(x['full']==x['cached'] and x['full_graph']==x['cached_graph'] for x in r['rows']))
if __name__=='__main__':unittest.main(verbosity=2)
