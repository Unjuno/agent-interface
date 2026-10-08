from __future__ import annotations
import copy,hashlib,json,unittest
import audit_a04_v2 as audit
class IdentityGuardAuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  audit.verify_v2_freeze();cls.freeze,cls.raw,cls.result,cls.scenario,fb,rb,zb=audit.load();cls.raw_sha=hashlib.sha256(rb).hexdigest();cls.freeze_sha=hashlib.sha256(fb).hexdigest()
 def test_retained_identity_matrix_passes(self):
  v=audit.audit(self.raw,self.result,self.freeze,self.scenario,self.raw_sha,self.freeze_sha)
  self.assertEqual(v["disposition"],"PASS_EXACT_CLEANUP_IDENTITY_GUARD_SCOPED")
 def test_contextualized_mismatch_mutation_is_rejected(self):
  raw=copy.deepcopy(self.raw);raw["successor"][0]["events"][0]["event"]="input_release_measurement"
  with self.assertRaisesRegex(audit.AuditFailure,"successor mismatch not unscoped"):
   audit.audit(raw,self.result,self.freeze,self.scenario,self.raw_sha,self.freeze_sha)
 def test_missing_mismatch_case_is_rejected(self):
  raw=copy.deepcopy(self.raw);raw["successor"].pop(0)
  with self.assertRaisesRegex(audit.AuditFailure,"case matrix/order mismatch"):
   audit.audit(raw,self.result,self.freeze,self.scenario,self.raw_sha,self.freeze_sha)
if __name__=="__main__":unittest.main(verbosity=2)
