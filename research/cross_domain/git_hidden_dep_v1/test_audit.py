import json,tempfile,unittest
from pathlib import Path
from experiment import one,deliver,setup_repo,TARGET,git,oid
from audit import audit_case
class T(unittest.TestCase):
 def make(self,p='complete_two_path',s='stable'):
  td=tempfile.TemporaryDirectory();d=Path(td.name)/'c';d.mkdir();one({'id':'x','rep':1,'policy':p,'schedule':s},d);return td,d
 def test_declared_only_misses_hidden(self):
  td,d=self.make('declared_only','hidden_changed');r=audit_case(d);self.assertFalse(r['ground_truth_correct']);td.cleanup()
 def test_complete_rejects_hidden(self):
  td,d=self.make('complete_two_path','hidden_changed');r=audit_case(d);self.assertTrue(r['ground_truth_correct']);td.cleanup()
 def test_complete_allows_unrelated(self):
  td,d=self.make('complete_two_path','unrelated_changed');r=audit_case(d);self.assertTrue(r['ground_truth_correct']);td.cleanup()
 def test_race_after_check_rejected(self):
  td=tempfile.TemporaryDirectory();repo=Path(td.name)/'r';A,B,C,D,E=setup_repo(repo);git(repo,'update-ref',TARGET,E,A)
  def mutate(_x): git(repo,'update-ref',TARGET,D,E)
  r=deliver(repo,'complete_two_path',A,B,before_cas=mutate);self.assertNotEqual(r['returncode'],0);self.assertEqual(oid(repo,TARGET),D);td.cleanup()
 def test_corrupt_detected(self):
  td,d=self.make();p=d/'result.json';r=json.loads(p.read_text());r['final_target']='0'*40;p.write_text(json.dumps(r));
  with self.assertRaises(AssertionError):audit_case(d)
  td.cleanup()
if __name__=='__main__':unittest.main()
