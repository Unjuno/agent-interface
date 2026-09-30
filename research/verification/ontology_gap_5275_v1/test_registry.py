"""Host-only construction tests for the ontology-gap detector."""
import unittest
from registry import classify

def valid_plan():
    return {"plan_version":"v0.1","checks":[{"primitive":"TARGET.IDENTITY_CURRENT","subject_ref":"target:x","evidence_role":"OBSERVATION_CURRENT","verifier_class":"deterministic_rule","version":"1.0"}]}

class DetectorTests(unittest.TestCase):
    def test_supported_plan_is_only_coverage_not_authority(self):
        self.assertEqual(classify(valid_plan()), "PLAN_COVERED")
        self.assertNotIn("authority", classify(valid_plan()))
    def test_unknown_primitive_yields(self):
        p=valid_plan(); p["checks"][0]["primitive"]="LEGAL.RETENTION_CURRENT"
        self.assertEqual(classify(p), "UNKNOWN_CHECK_REQUIRED")
    def test_unknown_evidence_role_yields(self):
        p=valid_plan(); p["checks"][0]["evidence_role"]="MODEL_ASSERTION_ONLY"
        self.assertEqual(classify(p), "UNKNOWN_CHECK_REQUIRED")
    def test_malformed_missing_subject_yields(self):
        p=valid_plan(); del p["checks"][0]["subject_ref"]
        self.assertEqual(classify(p), "UNKNOWN_CHECK_REQUIRED")
    def test_empty_checks_yield(self):
        self.assertEqual(classify({"plan_version":"v0.1","checks":[]}), "UNKNOWN_CHECK_REQUIRED")
    def test_stale_ir_version_yields(self):
        p=valid_plan(); p["plan_version"]="v9"
        self.assertEqual(classify(p), "UNKNOWN_CHECK_REQUIRED")
    def test_non_object_yields(self):
        self.assertEqual(classify(None), "UNKNOWN_CHECK_REQUIRED")

if __name__ == "__main__":
    unittest.main()
