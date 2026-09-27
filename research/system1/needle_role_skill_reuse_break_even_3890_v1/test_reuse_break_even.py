import json,unittest,sys
sys.path.insert(0,'.')
import reuse_break_even as r
from loader import validate
class ConstructionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with open('/inputs/expected.json',encoding='utf-8') as f: expected=json.load(f)
  cls.art,cls.sha=validate('/inputs/skill.json',expected); cls.expected=expected
 def test_package_digest_and_role_set(self): self.assertEqual(set(self.art['tensors']),{'A','B','C'}); self.assertEqual(len(self.sha),64)
 def test_role_scoped_inference_is_finite(self):
  for role in ('A','B','C'):
   models=r.instantiate(self.art,(role,))
   _,pred=r.score(models[role],role,self.expected['roles'][role]['inputs'][0]); self.assertIn(pred,range(4))
 def test_invalid_scope_controls_yield(self):
  checks,_=r.controls(self.art,self.sha,{'role':'A','scope_role':'A','generation':3788,'package_digest':self.sha,'input':[0.0]*8}); self.assertEqual([c['outcome'] for c in checks],['YIELD']*4)
if __name__=='__main__': unittest.main()
