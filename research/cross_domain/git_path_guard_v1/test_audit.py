import json,tempfile,unittest
from pathlib import Path
from experiment import one, deliver, oid, setup_repo, TARGET, git
from audit import audit_case

class T(unittest.TestCase):
    def make(self,policy='path_current_cas',schedule='stable'):
        td=tempfile.TemporaryDirectory(); root=Path(td.name); d=root/'c'; d.mkdir(); one({'id':'x','rep':1,'policy':policy,'schedule':schedule},d); return td,d
    def test_path_allows_unrelated(self):
        td,d=self.make('path_current_cas','unrelated_changed'); r=audit_case(d); self.assertTrue(r['ground_truth_correct']); td.cleanup()
    def test_tree_false_rejects_unrelated(self):
        td,d=self.make('tree_current_cas','unrelated_changed'); r=audit_case(d); self.assertFalse(r['ground_truth_correct']); td.cleanup()
    def test_path_rejects_dependency(self):
        td,d=self.make('path_current_cas','dependency_changed'); r=audit_case(d); self.assertTrue(r['ground_truth_correct']); td.cleanup()
    def test_race_after_check_rejected(self):
        td=tempfile.TemporaryDirectory(); repo=Path(td.name)/'repo'; A,B,C,D=setup_repo(repo); git(repo,'update-ref',TARGET,C,A)
        def mutate(_x): git(repo,'update-ref',TARGET,D,C)
        r=deliver(repo,'path_current_cas',A,B,before_cas=mutate)
        self.assertNotEqual(r['returncode'],0); self.assertEqual(oid(repo,TARGET),D); td.cleanup()
    def test_corrupt_final_detected(self):
        td,d=self.make(); p=d/'result.json'; r=json.loads(p.read_text()); r['final_target']='0'*40; p.write_text(json.dumps(r))
        with self.assertRaises(AssertionError): audit_case(d)
        td.cleanup()
if __name__=='__main__': unittest.main()
