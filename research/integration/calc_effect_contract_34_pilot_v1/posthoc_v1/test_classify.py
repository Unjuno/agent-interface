from __future__ import annotations
import unittest
from classify import classify

class ClassificationTests(unittest.TestCase):
 def setUp(self):
  self.raw={"program_completed":True,"cell_after_edit_live":7,"source_sha256_before":"same","source_sha256_after":"same"}
  self.audit={"independently_reopened_A1":0,"source_sha256_independent":"same","disposition":"STOP_CONSTRUCTION","errors":["no visible Calc window was detected"]}
 def test_unsaved_live_value_contradicts_saved_effect(self):
  r=classify(self.raw,self.audit); self.assertEqual(r["harness_completion"],"COMPLETED"); self.assertEqual(r["live_view_predicate"],"MATCH"); self.assertEqual(r["saved_effect"],"CONTRADICTED"); self.assertEqual(r["frozen_construction_gate"],"STOP_CONSTRUCTION")
 def test_changed_hash_is_unknown(self):
  self.assertEqual(classify(dict(self.raw,source_sha256_after="changed"),self.audit)["saved_effect"],"UNKNOWN")
 def test_missing_disk_value_is_unknown(self):
  self.assertEqual(classify(self.raw,dict(self.audit,independently_reopened_A1=None))["saved_effect"],"UNKNOWN")
 def test_matching_persisted_value_is_verified(self):
  self.assertEqual(classify(self.raw,dict(self.audit,independently_reopened_A1=7))["saved_effect"],"VERIFIED")
if __name__=="__main__": unittest.main()
