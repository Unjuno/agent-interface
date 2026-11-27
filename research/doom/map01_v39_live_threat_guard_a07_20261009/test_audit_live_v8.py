"""Synthetic tests of the admission/acknowledgement/release timeline."""
import pathlib,tempfile,unittest
from unittest import mock
from test_audit_live_v7 import ReleaseTimeTests
import audit_live_v7 as v7
import audit_live_v8 as v8

class AckTimeTests(unittest.TestCase):
    def fixture(self):
        h,e,d,s=ReleaseTimeTests().fixture()
        next(x for x in e if x['event']=='input_admission')['input_ack_ns']=95
        return h,e,d,s
    def audit(self,h,e,d,s,module=v8):
        return h.run_audit(e,d,s,auditor=module,result_name='AUDIT_V8.json' if module is v8 else 'AUDIT_V7.json')[0]
    def test_valid_timeline_passes_scoped(self):
        h,e,d,s=self.fixture(); result=self.audit(h,e,d,s)
        self.assertEqual(result['status'],'PASS'); self.assertFalse(result['formal_pass'])
    def test_release_before_ack_is_v7_false_pass_and_v8_fail(self):
        h,e,d,s=self.fixture(); next(x for x in e if x['event']=='input_admission')['input_ack_ns']=115
        self.assertEqual(self.audit(h,e,d,s,v7)['status'],'PASS')
        result=self.audit(h,e,d,s); self.assertEqual(result['status'],'FAIL')
        self.assertFalse(result['per_cancellation'][0]['input_release_timing_ok'])
    def test_missing_malformed_or_inconsistent_ack_fails(self):
        for ack in (None, True, '95', 89, 110, 115):
            with self.subTest(ack=ack):
                h,e,d,s=self.fixture(); next(x for x in e if x['event']=='input_admission')['input_ack_ns']=ack
                self.assertEqual(self.audit(h,e,d,s)['status'],'FAIL')
    def test_row_reordering_does_not_override_valid_times(self):
        h,e,d,s=self.fixture(); row=next(x for x in e if x['event']=='input_release_transition'); e.remove(row); e.insert(0,row)
        self.assertEqual(self.audit(h,e,d,s)['status'],'PASS')
    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory); result=root/'AUDIT_V8.json'; result.write_text('preserve')
            with mock.patch.object(v8,'ROOT',root), self.assertRaises(FileExistsError): v8.main()
            self.assertEqual(result.read_text(),'preserve')

if __name__=='__main__': unittest.main()
