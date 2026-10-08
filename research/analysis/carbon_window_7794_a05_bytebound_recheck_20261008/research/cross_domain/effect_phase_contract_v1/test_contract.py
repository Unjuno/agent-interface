import json,tempfile,unittest
from pathlib import Path
from experiment import run_case
from audit import audit_case

HERE=Path(__file__).parent
RECEIVER=HERE/'direct_receiver.py'
class T(unittest.TestCase):
    def one(self,klass,behavior):
        td=tempfile.TemporaryDirectory(); d=Path(td.name)/'c'; r=run_case({'id':'x','effect_class':klass,'behavior':behavior,'rep':0},d,RECEIVER); return td,d,r
    def test_stageable_wrong_no_effect(self):
        td,d,r=self.one('stageable','wrong'); a=audit_case(d); self.assertFalse(a['effect_present']); self.assertEqual(a['phase_label'],'REJECTED_PRE_EFFECT'); td.cleanup()
    def test_stageable_correct(self):
        td,d,r=self.one('stageable','correct'); self.assertEqual(audit_case(d)['phase_label'],'PUBLISHED_VERIFIED'); td.cleanup()
    def test_direct_wrong_persists(self):
        td,d,r=self.one('direct','wrong'); a=audit_case(d); self.assertTrue(a['effect_present']); self.assertEqual(a['phase_label'],'EFFECT_CONTRADICTED'); self.assertFalse(a['legacy_no_effect_claim_correct']); td.cleanup()
    def test_direct_correct(self):
        td,d,r=self.one('direct','correct'); self.assertEqual(audit_case(d)['phase_label'],'EFFECT_VERIFIED'); td.cleanup()
    def test_corruption_detected(self):
        td,d,r=self.one('stageable','correct'); p=d/'result.json'; x=json.loads(p.read_text()); x['effect_value']='wrong'; p.write_text(json.dumps(x));
        with self.assertRaises(AssertionError): audit_case(d)
        td.cleanup()
if __name__=='__main__': unittest.main()
