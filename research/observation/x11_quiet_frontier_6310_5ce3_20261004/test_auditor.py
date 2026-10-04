"""Saved preflight characterization only, not formal/native replay."""
import copy,json,unittest
from pathlib import Path
from auditor import verify
ROOT=Path(__file__).parent
class AuditorTests(unittest.TestCase):
    def setUp(self):
        self.row=json.loads((ROOT/'construction/native_preflight/raw.jsonl').read_text())
    def test_excluded_real_readiness_quiet(self):
        self.assertEqual(verify(self.row),{'pre_F_changed':False,'after_F_changed':False,'status':'QUIET_AS_OF_FRONTIER'})
    def test_bool_integer_not_coverage(self):
        self.row['subscription']['covered']=1
        with self.assertRaises(ValueError):verify(self.row)
    def test_authority_from_quiet_rejected(self):
        self.row['safe_to_act_at_B']=True
        with self.assertRaises(ValueError):verify(self.row)
    def test_missing_qualification_rejected(self):
        self.row['qualification_events'].pop()
        with self.assertRaises(ValueError):verify(self.row)
    def test_server_event_forgery_rejected(self):
        self.row['qualification_events'][0]['send_event']=True
        with self.assertRaises(ValueError):verify(self.row)
    def test_wrong_epoch_rejected(self):
        self.row['subscription']['epoch']='foreign'
        with self.assertRaises(ValueError):verify(self.row)
if __name__=='__main__':unittest.main()
