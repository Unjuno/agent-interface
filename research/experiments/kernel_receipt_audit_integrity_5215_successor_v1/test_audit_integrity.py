import unittest
from audit_integrity import audit, EXPECTED
BASE=dict(EXPECTED)
class AuditIntegrityTests(unittest.TestCase):
 def test_original_is_held_and_invalid_temporal_cases_are_named(self):
  got=audit(BASE)
  self.assertEqual(got["disposition"],"HOLD_LEGACY_PLAN_CONFLICT")
  self.assertEqual(got["errors"],[])
  self.assertEqual(set(got["inconsistent_cases"]),{"execution_end_999","execution_end_1000","execution_end_1001","effect_at_499","effect_at_699"})
 def test_missing_each_negative_field_is_rejected(self):
  for k in ("execution_end_1000","execution_end_1001","effect_at_499","effect_at_699"):
   d=dict(BASE);d.pop(k);self.assertIn("required_key_set_mismatch",audit(d)["errors"])
 def test_null_and_string_values_are_rejected(self):
  for v in (None,"true"):
   for k in ("execution_end_1000","execution_end_1001","effect_at_499","effect_at_699"):
    d=dict(BASE);d[k]=v;self.assertIn("non_boolean:"+k,audit(d)["errors"])
 def test_unexpected_key_is_rejected(self):
  d=dict(BASE);d["extra"]=False;self.assertIn("required_key_set_mismatch",audit(d)["errors"])
 def test_integer_is_not_boolean(self):
  d=dict(BASE);d["execution_end_1000"]=1;self.assertIn("non_boolean:execution_end_1000",audit(d)["errors"])
 def test_identity_negative_control_is_enforced(self):
  d=dict(BASE);d["execution_wrong_command"]=True;self.assertIn("outcome_mismatch:execution_wrong_command",audit(d)["errors"])
 def test_non_object_is_rejected(self):
  for d in (None,[],"record"):self.assertEqual(audit(d)["disposition"],"HOLD_SCHEMA")
 def test_mutation_suite_rejects_all_directed_corruptions(self):
  mutants=[]
  for k in ("execution_end_1000","execution_end_1001","effect_at_499","effect_at_699"):
   d=dict(BASE);d.pop(k);mutants.append(d)
   for v in (None,"true",1):
    d=dict(BASE);d[k]=v;mutants.append(d)
  d=dict(BASE);d["extra"]=False;mutants.append(d)
  d=dict(BASE);d["execution_wrong_command"]=True;mutants.append(d)
  for d in mutants:
   with self.subTest(record=d):self.assertTrue(audit(d)["errors"] or audit(d)["disposition"]=="HOLD_LEGACY_PLAN_CONFLICT")
if __name__=="__main__": unittest.main()
