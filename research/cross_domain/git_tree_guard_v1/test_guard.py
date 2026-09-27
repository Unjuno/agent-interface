import tempfile,unittest
from pathlib import Path
from experiment import one,setup,sh
from audit import audit_case
class T(unittest.TestCase):
 def mk(self,p,s):
  td=tempfile.TemporaryDirectory();d=Path(td.name)/'c';d.mkdir();r=one({'id':'x','rep':1,'policy':p,'schedule':s},d);return td,d,r
 def test_exact_false_reject_same_tree(self):
  td,d,r=self.mk('exact_old','semantic_same');audit_case(d);self.assertFalse(r['correct']);td.cleanup()
 def test_tree_accepts_same_tree(self):
  td,d,r=self.mk('tree_current_cas','semantic_same');audit_case(d);self.assertTrue(r['correct']);td.cleanup()
 def test_tree_rejects_different(self):
  td,d,r=self.mk('tree_current_cas','semantic_different');audit_case(d);self.assertTrue(r['correct']);td.cleanup()
 def test_current_oid_cas_closes_postcheck_race(self):
  td=tempfile.TemporaryDirectory();repo=Path(td.name)/'r';A,B,C,D,T=setup(repo);sh(repo,'git','update-ref','refs/heads/target',C);cur=sh(repo,'git','rev-parse','refs/heads/target').stdout.strip();self.assertEqual(sh(repo,'git','rev-parse',cur+'^{tree}').stdout.strip(),T);sh(repo,'git','update-ref','refs/heads/target',D);p=sh(repo,'git','update-ref','refs/heads/target',B,cur,check=False);self.assertNotEqual(p.returncode,0);self.assertEqual(sh(repo,'git','rev-parse','refs/heads/target').stdout.strip(),D);td.cleanup()
if __name__=='__main__':unittest.main()
