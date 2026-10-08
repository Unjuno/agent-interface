from __future__ import annotations
import json,unittest
from pathlib import Path
import probe_a04,audit_a04
HERE=Path(__file__).resolve().parent
class CleanupIdentityGuardTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.scenario=json.loads((HERE/"scenario.json").read_text())
  cls.old=probe_a04.load_backend(HERE/"SOURCE/A03/bridge_a03.py","identity_test_a03")
  cls.new=probe_a04.load_backend(HERE/"bridge_a04.py","identity_test_a04")
 def test_predecessor_false_contextualizes_mismatched_identity(self):
  for field in ("owner","intent","key","bracket"):
   with self.subTest(field=field):
    rows=probe_a04.run_one(self.old,self.scenario,field)
    self.assertEqual(rows["events"][0]["event"],"input_release_measurement")
    self.assertEqual(rows["context_count"],0)
 def test_successor_keeps_mismatches_unscoped_and_preserves_active_state(self):
  for field in ("owner","intent","key","bracket"):
   with self.subTest(field=field):
    rows=probe_a04.run_one(self.new,self.scenario,field)
    self.assertEqual(rows["events"][0]["event"],"input_cleanup_unscoped")
    self.assertEqual((rows["held"],rows["active_count"],rows["context_count"]),([self.scenario["key"]],1,1))
 def test_matching_cleanup_still_forwards_and_retires(self):
  rows=probe_a04.run_one(self.new,self.scenario,"valid")
  self.assertEqual(rows["events"][0]["event"],"input_release_measurement")
  self.assertEqual((rows["held"],rows["active_count"],rows["context_count"]),([],0,0))
if __name__=="__main__":unittest.main(verbosity=2)
