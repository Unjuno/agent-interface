import unittest
from audit_integrity import audit, EXPECTED_KEYS, expected_outcome
BASE={"execution_end_700":True,"execution_end_999":True,"execution_end_1000":True,"execution_end_1001":True,"execution_wrong_command":False,"effect_at_499":True,"effect_at_699":True,"effect_at_700":True,"effect_at_701":True}
class AuditIntegrityTests(unittest.TestCase):
 def test_legacy_record_is_held_with_five_derived_mismatches(self):
  got=audit(BASE); self.assertEqual(got["disposition"],"HOLD_LEGACY_PLAN_CONFLICT")
  self.assertEqual(set(got["case_mismatches"]),{"execution_end_999","execution_end_1000","execution_end_1001","effect_at_499","effect_at_699"})
 def test_each_required_negative_field_missing_is_error(self):
  for k in ("execution_end_1000","execution_end_1001","effect_at_499","effect_at_699"):
   d=dict(BASE);d.pop(k);self.assertIn("required_key_set_mismatch",audit(d)["errors"])
 def test_null_string_and_integer_are_rejected(self):
  for value in (None,"true",1):
   for k in ("execution_end_1000","execution_end_1001","effect_at_499","effect_at_699"):
    d=dict(BASE);d[k]=value;self.assertIn("non_boolean:"+k,audit(d)["errors"])
 def test_extra_key_rejected(self):
  d=dict(BASE);d["extra"]=False;self.assertIn("required_key_set_mismatch",audit(d)["errors"])
 def test_identity_negative_control_flip_detected(self):
  d=dict(BASE);d["execution_wrong_command"]=True;self.assertIn("execution_wrong_command",audit(d)["case_mismatches"])
 def test_each_derived_outcome_flip_detected(self):
  for k in sorted(EXPECTED_KEYS-{"execution_wrong_command"}):
   d=dict(BASE);d[k]=expected_outcome(k);self.assertNotIn(k,audit(d)["case_mismatches"])
   d[k]=not expected_outcome(k);self.assertIn(k,audit(d)["case_mismatches"])
 def test_non_object_records_rejected(self):
  for record in (None,[],"record"):self.assertEqual(audit(record)["disposition"],"HOLD_SCHEMA")
 def test_mutation_census_is_exact(self):
  mutants=[]
  for k in ("execution_end_1000","execution_end_1001","effect_at_499","effect_at_699"):
   d=dict(BASE);d.pop(k);mutants.append(d)
   for v in (None,"true",1):
    d=dict(BASE);d[k]=v;mutants.append(d)
  d=dict(BASE);d["extra"]=False;mutants.append(d)
  d=dict(BASE);d["execution_wrong_command"]=True;mutants.append(d)
  self.assertEqual(len(mutants),18)
  for d in mutants:self.assertTrue(audit(d)["errors"] or audit(d)["case_mismatches"])
if __name__=="__main__":unittest.main()
