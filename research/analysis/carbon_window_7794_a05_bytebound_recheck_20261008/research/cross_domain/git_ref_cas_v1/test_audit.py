import json, tempfile, unittest
from pathlib import Path
from experiment import one
from audit import audit_case

class T(unittest.TestCase):
    def make(self,policy='cas',schedule='stable'):
        td=tempfile.TemporaryDirectory(); root=Path(td.name); d=root/'c'; d.mkdir()
        one({'id':'x','rep':1,'policy':policy,'schedule':schedule},d); return td,d
    def test_valid(self):
        td,d=self.make(); audit_case(d); td.cleanup()
    def test_target_changed_cas(self):
        td,d=self.make('cas','target_changed'); r=audit_case(d); self.assertTrue(r['correct']); self.assertNotEqual(r['returncode'],0); td.cleanup()
    def test_target_changed_naive_is_retained_negative(self):
        td,d=self.make('naive','target_changed'); r=audit_case(d); self.assertFalse(r['correct']); self.assertEqual(r['final_target'],r['B']); td.cleanup()
    def test_unrelated_survives(self):
        td,d=self.make('cas','unrelated_changed'); r=audit_case(d); self.assertEqual(r['final_other'],r['C']); td.cleanup()
    def test_corrupt_final_detected(self):
        td,d=self.make(); p=d/'result.json'; r=json.loads(p.read_text()); r['final_target']='0'*40; p.write_text(json.dumps(r))
        with self.assertRaises(AssertionError): audit_case(d)
        td.cleanup()
    def test_corrupt_rc_detected(self):
        td,d=self.make('cas','target_changed'); p=d/'result.json'; r=json.loads(p.read_text()); r['returncode']=0; p.write_text(json.dumps(r))
        with self.assertRaises(AssertionError): audit_case(d)
        td.cleanup()
if __name__=='__main__':unittest.main()
