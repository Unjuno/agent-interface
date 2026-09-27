import json,tempfile,unittest
from pathlib import Path
from experiment import one
from audit import audit_case

class T(unittest.TestCase):
    def make(self,policy='observed_readset',schedule='stable'):
        td=tempfile.TemporaryDirectory(); d=Path(td.name)/'c'; r=one({'id':'x','rep':1,'policy':policy,'schedule':schedule},d); return td,d,r
    def test_observed_hidden_rejects(self):
        td,d,r=self.make('observed_readset','hidden_changed'); audit_case(d); self.assertNotEqual(r['returncode'],0); td.cleanup()
    def test_planner_hidden_is_unsound(self):
        td,d,r=self.make('planner_declared','hidden_changed'); audit_case(d); self.assertFalse(r['ground_truth_correct']); td.cleanup()
    def test_unrelated_allowed(self):
        td,d,r=self.make('observed_readset','unrelated_changed'); audit_case(d); self.assertTrue(r['ground_truth_correct']); td.cleanup()
    def test_declared_change_rejected_both(self):
        for p in ['planner_declared','observed_readset']:
            td,d,r=self.make(p,'declared_changed'); audit_case(d); self.assertEqual(r['returncode'],97); td.cleanup()
    def test_corrupt_readset_detected(self):
        td,d,r=self.make(); p=d/'result.json'; x=json.loads(p.read_text()); x['plan_read_set']=x['plan_read_set'][:1]; p.write_text(json.dumps(x))
        with self.assertRaises(AssertionError): audit_case(d)
        td.cleanup()

if __name__=='__main__':unittest.main()
