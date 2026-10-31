"""Synthetic v6/v7 comparison; no historical allocation is read."""
import pathlib, tempfile, unittest
from unittest import mock
from test_audit_live_v6_token import V6TokenTests
import audit_live_v6 as v6
import audit_live_v7 as v7

class ReleaseTimeTests(unittest.TestCase):
    def fixture(self):
        h,e,d,s=V6TokenTests().fixture()
        next(x for x in e if x['event']=='input_release_transition').update(
            release_call_started_ns=110,release_call_returned_ns=120)
        return h,e,d,s
    def run_version(self,h,e,d,s,module):
        return h.run_audit(e,d,s,auditor=module,result_name='AUDIT_V7.json' if module is v7 else 'AUDIT_V6.json')[0]
    def test_valid_timing_passes_and_keeps_formal_false(self):
        h,e,d,s=self.fixture(); result=self.run_version(h,e,d,s,v7)
        self.assertEqual(result['status'],'PASS'); self.assertFalse(result['formal_pass'])
    def test_earlier_release_is_v6_false_pass_and_v7_fail(self):
        h,e,d,s=self.fixture(); row=next(x for x in e if x['event']=='input_release_transition')
        row.update(release_call_started_ns=80,release_call_returned_ns=85)
        self.assertEqual(self.run_version(h,e,d,s,v6)['status'],'PASS')
        result=self.run_version(h,e,d,s,v7)
        self.assertEqual(result['status'],'FAIL'); self.assertFalse(result['per_cancellation'][0]['input_release_timing_ok'])
    def test_absent_malformed_equal_or_reversed_times_fail_closed(self):
        for start,end in [(None,120),(True,120),('110',120),(90,120),(110,None),(110,109)]:
            with self.subTest(start=start,end=end):
                h,e,d,s=self.fixture(); row=next(x for x in e if x['event']=='input_release_transition')
                row.update(release_call_started_ns=start,release_call_returned_ns=end)
                self.assertEqual(self.run_version(h,e,d,s,v7)['status'],'FAIL')
    def test_delayed_row_order_with_valid_timestamps_can_pass(self):
        h,e,d,s=self.fixture(); row=next(x for x in e if x['event']=='input_release_transition')
        e.remove(row); e.insert(0,row)
        self.assertEqual(self.run_version(h,e,d,s,v7)['status'],'PASS')
    def test_unknown_identity_and_duplicate_transition_still_fail(self):
        for mode in ('unknown','duplicate'):
            with self.subTest(mode=mode):
                h,e,d,s=self.fixture(); row=next(x for x in e if x['event']=='input_release_transition')
                if mode=='unknown': row['intent_token']='other'
                else: e.append(dict(row))
                self.assertNotEqual(self.run_version(h,e,d,s,v7)['status'],'PASS')
    def test_existing_result_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory); result=root/'AUDIT_V7.json'; result.write_text('preserve')
            with mock.patch.object(v7,'ROOT',root), self.assertRaises(FileExistsError): v7.main()
            self.assertEqual(result.read_text(),'preserve')

if __name__=='__main__': unittest.main()
