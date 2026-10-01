import json,unittest
from pathlib import Path
import study
ROOT=Path(__file__).resolve().parent
TRACE=json.loads((ROOT/'trace.json').read_text())
class T(unittest.TestCase):
 def test_trace_shape(self): self.assertEqual((len(TRACE),TRACE[0]['name'],TRACE[-1]['name']),(12,'BASE','PRODUCER_VERSION_CHANGE'))
 def test_hidden_flip_changes_oracle(self):
  self.assertEqual(study.oracle('READY_TO_SUBMIT',TRACE[0]),'TRUE'); self.assertEqual(study.oracle('READY_TO_SUBMIT',TRACE[2]),'FALSE')
 def test_incomplete_key_omits_risk(self):
  k=study.cache_key('DECLARED_ONLY','READY_TO_SUBMIT',TRACE[2]); self.assertEqual(k['dependency_generations'],{'form':1})
 def test_complete_key_binds_risk(self):
  k=study.cache_key('COMPLETE_DECLARATION','READY_TO_SUBMIT',TRACE[2]); self.assertEqual(k['dependency_generations'],{'form':1,'risk':2})
 def test_unrelated_change_same_semantics(self):
  self.assertEqual({p:study.oracle(p,TRACE[0]) for p in study.SPECS},{p:study.oracle(p,TRACE[1]) for p in study.SPECS})
 def test_aba_value_restores_generation_changes(self):
  self.assertEqual(TRACE[0]['values']['risk'],TRACE[4]['values']['risk']); self.assertNotEqual(TRACE[0]['generations']['risk'],TRACE[4]['generations']['risk'])
 def test_graph(self): self.assertEqual(study.graph({'READY_TO_SUBMIT':'TRUE','TARGET_MATCH':'TRUE'}),'SUBMIT_READY')
if __name__=='__main__': unittest.main(verbosity=2)
