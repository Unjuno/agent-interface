"""Pure offline contract tests. Does not load libX11 or execute actors."""
import copy,hashlib,json,unittest
from pathlib import Path
from predecessor_policy import classify
HERE=Path(__file__).resolve().parent
class Contract(unittest.TestCase):
    def packet(self):return dict(epoch='e',expected_epoch='e',window=100,keycode=50,seed_keymap='00'*32,seed_focused=True,first_ordinal=0,events=[],coverage_complete=True)
    def down(self):return dict(ordinal=0,type=2,send_event=False,window=100,keycode=50)
    def test_up(self):self.assertEqual(classify(self.packet(),'FOCUS_KEYMAP')['status'],'TYPE')
    def test_down(self):
        p=self.packet();p['events']=[self.down()];self.assertEqual(classify(p,'FOCUS_KEYMAP')['status'],'WAIT')
    def test_missing_coverage(self):
        p=self.packet();p['coverage_complete']=False;self.assertEqual(classify(p,'FOCUS_KEYMAP')['status'],'UNKNOWN')
    def test_foreign_epoch(self):
        p=self.packet();p['epoch']='foreign';self.assertEqual(classify(p,'FOCUS_KEYMAP')['status'],'UNKNOWN')
    def test_bool_key(self):
        p=self.packet();p['keycode']=True;self.assertEqual(classify(p,'FOCUS_KEYMAP')['status'],'UNKNOWN')
    def test_gap(self):
        p=self.packet();e=self.down();e['ordinal']=1;p['events']=[e];self.assertEqual(classify(p,'FOCUS_KEYMAP')['status'],'UNKNOWN')
    def test_synthetic(self):
        p=self.packet();e=self.down();e['send_event']=True;p['events']=[e];self.assertEqual(classify(p,'FOCUS_KEYMAP')['status'],'UNKNOWN')
    def test_no_mutation(self):
        p=self.packet();p['events']=[self.down()];old=copy.deepcopy(p);classify(p,'FOCUS_KEYMAP');self.assertEqual(p,old)
    def test_lineage(self):
        d=json.loads((HERE/'LINEAGE.json').read_bytes())
        for n,h in d['unchanged_files'].items():self.assertEqual(hashlib.sha256((HERE/n).read_bytes()).hexdigest(),h)
        self.assertEqual(hashlib.sha256((HERE/'acquire.c').read_bytes()[:d['native_prefix_bytes']]).hexdigest(),d['native_prefix_sha256'])
    def test_modes_source(self):
        s=(HERE/'bundle.py').read_text();self.assertIn("'FOCUS_PIGGYBACK':'LOCAL_ONLY'",s);self.assertIn("'FOCUS_SYNC':'EVENT_SYNC'",s)
if __name__=='__main__':unittest.main()
