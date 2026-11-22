from __future__ import annotations
import copy, hashlib, json, unittest
import audit_a04_v2 as audit

class ExactTypeOwnerAuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  audit.verify_v2_freeze()
  cls.old=audit.load_old();cls.freeze,cls.raw,cls.result=cls.old.load_frozen();cls.oracle=staticmethod(cls.old.load_oracle())
 def assert_alias_rejected(self,mutate):
  raw=copy.deepcopy(self.raw);up=next(e for e in raw["events"] if e.get("event")=="input_release_measurement")
  mutate(raw,up)
  result=copy.deepcopy(self.result)
  result["raw_sha256"]=hashlib.sha256((json.dumps(raw,sort_keys=True,indent=2)+"\n").encode()).hexdigest()
  with self.assertRaises(audit.AuditFailure):
   audit.strict_source_audit(raw,result,self.freeze,self.oracle)
 def test_retained_owner_trace_passes(self):
  v=audit.strict_source_audit(self.raw,self.result,self.freeze,self.oracle)
  self.assertEqual(v["status"],"PASS_OWNER_SOURCE_BOUND_EXACT_TYPE_AUDIT")
 def test_nested_bool_integer_alias_in_projected_bracket_rejected(self):
  raw=copy.deepcopy(self.raw);up=next(e for e in raw["events"] if e.get("event")=="input_release_measurement")
  up["physical_key_measurement"]["bracket"]["grants_input_authority"]=0
  result=copy.deepcopy(self.result)
  result["raw_sha256"]=hashlib.sha256((json.dumps(raw,sort_keys=True,indent=2)+"\n").encode()).hexdigest()
  old_result=self.old.strict_source_audit(raw,result,self.freeze,lambda rows:self.oracle(rows))
  self.assertEqual(old_result["status"],"PASS_OWNER_SOURCE_BOUND_CLEANUP_AUDIT")
  with self.assertRaisesRegex(audit.AuditFailure,"exact JSON type or value"):
   audit.strict_source_audit(raw,result,self.freeze,self.oracle)
if __name__=="__main__":unittest.main(verbosity=2)
