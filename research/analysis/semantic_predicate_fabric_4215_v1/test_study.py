import unittest
import backend,cases,oracle
class T(unittest.TestCase):
 def test_case_count(self):self.assertEqual(len(cases.CASES),20)
 def test_backend_oracle_predicates(self):
  for c in cases.CASES:self.assertEqual(backend.predicate_forward(c['features']),oracle.labels(c['features']))
 def test_direct_oracle(self):
  for c in cases.CASES:self.assertEqual(backend.direct_forward(c['features']),oracle.disposition(oracle.labels(c['features'])))
 def test_unknown(self):self.assertEqual(backend.predicate_forward(cases.CASES[8]['features'])['TARGET_CORRECT'],'UNKNOWN')
 def test_same_state_different_intent(self):
  self.assertEqual(cases.CASES[0]['features']['target_pos'],cases.CASES[1]['features']['target_pos']);self.assertNotEqual(backend.direct_forward(cases.CASES[0]['features']),backend.direct_forward(cases.CASES[1]['features']))
 def test_irrelevant(self):self.assertEqual(backend.direct_forward(cases.CASES[0]['features']),backend.direct_forward(cases.CASES[7]['features']))
 def test_reuse(self):
  pred=backend.predicate_forward(cases.CASES[0]['features']);_,reads=backend.graph(pred);self.assertGreater(reads.count('TARGET_CORRECT'),1)
if __name__=='__main__':unittest.main(verbosity=2)
