"""Real persisted-record behavior; expectations are literal, not policy-derived."""
import json,tempfile,unittest
from pathlib import Path
from policy import learn,decide

class PolicyTests(unittest.TestCase):
    def record(self,path):
        learn(path,'target','click_then_F8',{'focus':False},'focus','event-evidence')
    def test_record_reloads_instead_of_ignoring_memory(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'memory.json';self.record(p)
            self.assertEqual(decide('TYPED',p,{'focus':False},'target','click_then_F8'),'BLOCK')
    def test_cleared_failure_does_not_permanently_block(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'memory.json';self.record(p)
            self.assertEqual(decide('TYPED',p,{'focus':True},'target','click_then_F8'),'TRY')
    def test_withheld_field_is_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'memory.json';self.record(p)
            self.assertEqual(decide('TYPED',p,{'focus':None},'target','click_then_F8'),'UNKNOWN')
    def test_scope_change_invalidates_record(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'memory.json';self.record(p)
            self.assertEqual(decide('TYPED',p,{'focus':True},'other','click_then_F8'),'UNKNOWN')
    def test_full_guard_catches_different_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'memory.json';self.record(p)
            obs={'cover':True,'geometry':True,'focus':True,'pending':False,'business':True}
            self.assertEqual(decide('TYPED',p,obs,'target','click_then_F8'),'TRY')
            self.assertEqual(decide('TYPED_PLUS_FRESH',p,obs,'target','click_then_F8'),'BLOCK')
    def test_non_boolean_guard_value_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'memory.json';self.record(p)
            obs={k:True for k in ('cover','geometry','focus','pending','business')};obs['focus']=1
            self.assertEqual(decide('FRESH',p,obs,'target','click_then_F8'),'UNKNOWN')
    def test_first_record_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'memory.json';self.record(p)
            with self.assertRaises(FileExistsError):self.record(p)
            self.assertEqual(json.loads(p.read_text())['observed_preconditions'],{'focus':False})
    def test_fresh_guard_requires_no_memory_file(self):
        with tempfile.TemporaryDirectory() as d:
            absent=Path(d)/'absent.json'
            self.assertEqual(decide('FRESH',absent,{k:True for k in ('cover','geometry','focus','pending','business')},'target','click_then_F8'),'TRY')

if __name__=='__main__':unittest.main()
