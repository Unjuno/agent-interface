import json
import unittest

from candidate import run
from audit import verify


class CredentialPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open("fixture.json", encoding="utf-8") as stream:
            cls.fixture = json.load(stream)
        cls.raw = run(cls.fixture)

    def test_case_policy_cartesian_product(self):
        self.assertEqual(len(self.raw["rows"]), 75)
        self.assertEqual(len({(r["case_id"], r["policy"]) for r in self.raw["rows"]}), 75)

    def test_broker_fails_closed_on_boundaries(self):
        rows = {r["case_id"]: r for r in self.raw["rows"] if r["policy"] == "request_bound_broker"}
        for case_id in ("lookalike_wrong_origin", "origin_swap_after_capture", "stale_target_generation", "expired_handle", "replayed_handle", "focus_redirect_field_replaced", "protected_path_unavailable", "missing_user_authorization", "credential_account_scope_mismatch", "credential_purpose_scope_mismatch"):
            self.assertNotEqual(rows[case_id]["decision"], "DELIVERED_TO_BOUND_TARGET")
        self.assertEqual(rows["embedded_origin_unavailable"]["decision"], "UNKNOWN_ORIGIN_SCOPE")
        self.assertEqual(rows["preexisting_authenticated_session"]["decision"], "NO_ACTION_ALREADY_AUTHENTICATED")

    def test_delivery_is_not_effect_and_prior_session_is_unattributed(self):
        rows = {r["case_id"]: r for r in self.raw["rows"] if r["policy"] == "request_bound_broker"}
        self.assertEqual(rows["effect_oracle_absent"]["effect_status"], "UNKNOWN_DELIVERY")
        self.assertEqual(rows["masked_ack_without_server_effect"]["effect_status"], "UNKNOWN_DELIVERY")
        self.assertEqual(rows["preexisting_authenticated_session"]["effect_status"], "UNATTRIBUTED_PREEXISTING_SESSION")

    def test_agent_typing_is_planner_exposed_and_visual_clone_can_misdirect(self):
        for r in self.raw["rows"]:
            if r["policy"] in ("actor_only_typing", "visual_only_typing"):
                self.assertTrue(r["planner_secret_exposed"])
        r = next(r for r in self.raw["rows"] if r["case_id"] == "lookalike_wrong_origin" and r["policy"] == "visual_only_typing")
        self.assertTrue(r["wrong_origin_recipient"])

    def test_provider_documentation_unknowns_are_not_filled_in(self):
        rows = {r["case_id"]: r for r in self.raw["rows"] if r["policy"] == "documented_provider_profile"}
        self.assertEqual(rows["valid_bound_effect"]["decision"], "DELIVERED_TO_BOUND_TARGET")
        self.assertEqual(rows["replayed_handle"]["decision"], "UNKNOWN_PROVIDER_POLICY")
        self.assertEqual(rows["embedded_origin_unavailable"]["decision"], "UNKNOWN_ORIGIN_SCOPE")
        self.assertEqual(rows["credential_account_scope_mismatch"]["decision"], "UNKNOWN_PROVIDER_POLICY")

    def test_manual_fallback_never_claims_automation(self):
        rows = {r["case_id"]: r for r in self.raw["rows"] if r["policy"] == "no_automation_manual"}
        self.assertEqual(rows["lookalike_wrong_origin"]["decision"], "NOT_AUTOMATED")
        self.assertEqual(rows["valid_bound_effect"]["decision"], "DELIVERED_TO_HUMAN_VERIFIED_TARGET")

    def test_independent_oracle_and_mutations(self):
        errors, controls = verify(self.raw, self.fixture)
        self.assertEqual(errors, [])
        self.assertEqual(controls, {"rows":75,"expected_rows":75,"mutation_controls_rejected":8,"mutation_controls_total":8})


if __name__ == "__main__":
    unittest.main()
