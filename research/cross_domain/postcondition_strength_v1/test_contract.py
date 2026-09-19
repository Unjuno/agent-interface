import json,tempfile,unittest
from pathlib import Path
from experiment import one
from audit import audit_case
class T(unittest.TestCase):
  def runone(self,p,s):
    td=tempfile.TemporaryDirectory(); d=Path(td.name); r=one(d,{'id':'r01-'+p+'-'+s,'rep':1,'policy':p,'scenario':s}); audit_case(d/r['id']); return td,r
  def test_correct(self):
    t,r=self.runone('full_entry','correct'); self.assertEqual(r['reason'],'applied'); t.cleanup()
  def test_bytes_only_mode_false_accept(self):
    t,r=self.runone('bytes_only','wrong_mode'); self.assertEqual(r['reason'],'applied'); self.assertFalse(r['ground_truth_correct']); t.cleanup()
  def test_full_rejects_mode(self):
    t,r=self.runone('full_entry','wrong_mode'); self.assertEqual(r['reason'],'entry_postcondition_mismatch'); t.cleanup()
  def test_full_rejects_kind(self):
    t,r=self.runone('full_entry','wrong_kind'); self.assertEqual(r['reason'],'entry_postcondition_mismatch'); t.cleanup()
  def test_wrong_bytes_both_reject(self):
    t,r=self.runone('bytes_only','wrong_bytes'); self.assertEqual(r['reason'],'bytes_postcondition_mismatch'); t.cleanup()
  def test_write_conflict(self):
    t,r=self.runone('full_entry','write_conflict'); self.assertEqual(r['reason'],'write_conflict'); t.cleanup()
  def test_race(self):
    t,r=self.runone('full_entry','ref_race'); self.assertEqual(r['reason'],'cas_rejected'); t.cleanup()
if __name__=='__main__': unittest.main()
