import json,tempfile,unittest
from pathlib import Path
from experiment import one
from audit import audit_case
class T(unittest.TestCase):
    def make(self,p='all_traced',s='stable'):
        td=tempfile.TemporaryDirectory(); d=Path(td.name)/'c'; r=one({'id':'x','rep':1,'policy':p,'schedule':s},d); return td,d,r
    def test_all_traced_hidden_reject(self):
        td,d,r=self.make('all_traced','hidden_changed'); audit_case(d); self.assertTrue(r['ground_truth_correct']); td.cleanup()
    def test_bypass_hidden_stale(self):
        td,d,r=self.make('hidden_bypass','hidden_changed'); audit_case(d); self.assertFalse(r['ground_truth_correct']); td.cleanup()
    def test_bypass_receipt_missing_hidden(self):
        td,d,r=self.make('hidden_bypass','stable'); self.assertEqual([x['path'] for x in r['plan_read_set']],['declared.txt']); td.cleanup()
    def test_unrelated_allowed(self):
        for p in ['all_traced','hidden_bypass']:
            td,d,r=self.make(p,'unrelated_changed'); audit_case(d); self.assertTrue(r['ground_truth_correct']); td.cleanup()
    def test_corruption_detected(self):
        td,d,r=self.make(); p=d/'result.json'; x=json.loads(p.read_text()); x['plan_read_set']=[]; p.write_text(json.dumps(x));
        with self.assertRaises(AssertionError): audit_case(d)
        td.cleanup()
if __name__=='__main__':unittest.main()
