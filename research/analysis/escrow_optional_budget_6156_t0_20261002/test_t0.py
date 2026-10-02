import copy
import unittest
import audit
import candidate

RESULT = candidate.run()

class TestEscrowFiniteT0(unittest.TestCase):
    def test_independent_full_state_enumeration(self):
        self.assertEqual(audit.audit(RESULT)["status"], "PASS_METHOD_SCOPED")
        self.assertGreater(RESULT["enumeration"]["reachable_states"], 1000)

    def test_balanced_demand_reduces_per_use_coordination(self):
        c = RESULT["controls"]["balanced"]
        self.assertEqual(c["central_per_use_roundtrips"], 4)
        self.assertEqual(c["escrow_setup_roundtrips"], 2)
        self.assertEqual(c["escrow_optional_completed"], c["central_optional_completed"])

    def test_skewed_demand_exposes_stranded_rights_cost(self):
        c = RESULT["controls"]["skew"]
        self.assertEqual(c["escrow_optional_completed"], 2)
        self.assertEqual(c["central_optional_completed"], 4)
        self.assertEqual(c["stranded_rights"], 2)

    def test_crash_does_not_reclaim_without_fenced_surrender(self):
        c = RESULT["controls"]["heartbeat_reclaim"]
        self.assertEqual(c["required"], "FENCED_SURRENDER_REQUIRED")
        self.assertGreater(c["mutant_actual_consumes"], c["global_budget"])

    def test_restart_rejects_old_generation(self):
        c = RESULT["controls"]["stale_restart"]
        self.assertFalse(c["old_ticket_accepted"])
        self.assertEqual(c["current_generation"], 1)

    def test_duplicate_and_delayed_transfer_acks_are_idempotent(self):
        c = RESULT["controls"]["fenced_transfer"]
        self.assertTrue(c["first_ack_accepted"])
        self.assertFalse(c["duplicate_ack_accepted"])
        self.assertFalse(c["delayed_old_ack_accepted"])
        self.assertEqual(c["owner_after_old_ack"], "B")
        self.assertTrue(c["transfer_ids_distinct"])

    def test_mandatory_lane_survives_optional_exhaustion(self):
        c = RESULT["controls"]["mandatory_after_optional_exhaustion"]
        self.assertEqual(c["mandatory_verifier_served"], c["mandatory_verifier_capacity"])
        self.assertFalse(c["consequential_action_allowed_before_verifier"])
        self.assertEqual(RESULT["controls"]["mandatory_unavailable"]["disposition"], "YIELD")

    def test_role_is_derived_from_contract_not_self_label(self):
        c = RESULT["controls"]["role_ambiguity"]
        self.assertEqual(c["ambiguous"], "HOLD_ROLE_AMBIGUOUS")
        self.assertEqual(c["stale_self_labeled_optional"], "MANDATORY_VERIFIER")
        self.assertEqual(c["routine_self_labeled_mandatory"], "OPTIONAL_RECAPTURE")

    def test_auditor_rejects_over_budget_mutant(self):
        x = copy.deepcopy(RESULT)
        x["controls"]["heartbeat_reclaim"]["mutant_actual_consumes"] = 4
        self.assertEqual(audit.audit(x)["status"], "FAIL_METHOD_SCOPED")

    def test_auditor_rejects_suppressed_mandatory_verifier(self):
        x = copy.deepcopy(RESULT)
        x["controls"]["mandatory_after_optional_exhaustion"]["mandatory_verifier_served"] = 0
        self.assertEqual(audit.audit(x)["status"], "FAIL_METHOD_SCOPED")

    def test_auditor_rejects_false_transfer_ack_acceptance(self):
        x = copy.deepcopy(RESULT)
        x["controls"]["fenced_transfer"]["delayed_old_ack_accepted"] = True
        self.assertEqual(audit.audit(x)["status"], "FAIL_METHOD_SCOPED")

    def test_auditor_rejects_role_laundering(self):
        x = copy.deepcopy(RESULT)
        x["controls"]["role_ambiguity"]["routine_self_labeled_mandatory"] = "MANDATORY_VERIFIER"
        self.assertEqual(audit.audit(x)["status"], "FAIL_METHOD_SCOPED")

    def test_auditor_rejects_reachable_state_digest_corruption(self):
        x = copy.deepcopy(RESULT)
        x["enumeration"]["states_sha256"] = "0" * 64
        self.assertEqual(audit.audit(x)["status"], "FAIL_METHOD_SCOPED")

if __name__ == "__main__":
    unittest.main()
