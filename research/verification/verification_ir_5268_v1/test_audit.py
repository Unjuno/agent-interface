import unittest

from audit import audit_plan


BASE = {
    "schema": "verification_ir.v0.1",
    "unknown_check_required": False,
    "checks": [
        {"check_id":"target.current","primitive":"TARGET.IDENTITY_CURRENT","subject_ref":"window:save",
         "criticality":"MANDATORY","required_evidence_role":"CURRENT_OBSERVATION",
         "verifier_class":"fresh_target_observer","dependencies":[],"deadline":None,
         "budget_class":"bounded","fallback":"YIELD_NO_INPUT"},
        {"check_id":"intent.match","primitive":"SEMANTIC.INTENT_MATCH","subject_ref":"intent:save-v1",
         "criticality":"MANDATORY","required_evidence_role":"CURRENT_INTENT",
         "verifier_class":"intent_contract","dependencies":["target.current"],"deadline":None,
         "budget_class":"bounded","fallback":"YIELD_NO_INPUT"},
    ],
}


class IndependentOracleTests(unittest.TestCase):
    def test_independent_oracle_accepts_hand_derived_baseline_plan(self):
        self.assertTrue(audit_plan("iid-baseline", BASE))

    def test_independent_oracle_rejects_omission_role_change_dependency_loss_and_authority(self):
        omitted = {**BASE, "checks": BASE["checks"][:1]}
        wrong_role = {**BASE, "checks": [BASE["checks"][0], {**BASE["checks"][1],
            "required_evidence_role":"HISTORICAL_OBSERVATION"}]}
        no_dependency = {**BASE, "checks": [BASE["checks"][0], {**BASE["checks"][1],
            "dependencies":[]}]}
        authority = {**BASE, "authority":"GRANTED"}
        for mutation in (omitted, wrong_role, no_dependency, authority):
            with self.subTest(mutation=mutation):
                self.assertFalse(audit_plan("iid-baseline", mutation))


if __name__ == "__main__":
    unittest.main()
