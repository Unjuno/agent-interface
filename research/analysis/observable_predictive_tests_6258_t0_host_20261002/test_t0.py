import unittest

import audit
import candidate


class ObservablePredictiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = candidate.run()

    def test_silent_effect_alias_is_held_without_independent_effect_channel(self):
        case = self.result["cases"]["silent_effect_alias"]
        self.assertTrue(case["predictions_equal_within_horizon"])
        self.assertEqual(case["decision"], "HOLD_NOT_IDENTIFIABLE")
        self.assertFalse(case["merge_authorized"])

    def test_fresh_independent_receipt_keeps_different_histories_separate(self):
        case = self.result["cases"]["fresh_independent_receipt"]
        self.assertFalse(case["predictions_equal_within_horizon"])
        self.assertEqual(case["decision"], "KEEP_SEPARATE")

    def test_null_effect_complete_case_merges_only_equal_safe_profiles(self):
        case = self.result["cases"]["null_same_safe_continuation"]
        self.assertEqual(case["decision"], "MERGE_WITHIN_HORIZON")
        self.assertTrue(case["merge_authorized"])

    def test_finite_horizon_merge_does_not_claim_unbounded_equivalence(self):
        case = self.result["cases"]["delayed_beyond_horizon"]
        self.assertEqual(case["decision"], "MERGE_WITHIN_HORIZON")
        self.assertEqual(case["beyond_horizon"], "UNKNOWN")
        self.assertFalse(case["unbounded_equivalence"])

    def test_forbidden_probe_is_never_issued_or_used_as_evidence(self):
        case = self.result["cases"]["forbidden_probe_only_distinguishes"]
        self.assertEqual(case["decision"], "HOLD_NOT_IDENTIFIABLE")
        self.assertEqual(case["forbidden_probe_execution_count"], 0)
        self.assertNotIn("forbidden_write_probe", case["issued_tests"])

    def test_stale_and_source_correlated_receipts_do_not_complete_effect_channel(self):
        stale = self.result["cases"]["stale_receipt"]
        correlated = self.result["cases"]["source_correlated_receipt"]
        self.assertEqual(stale["decision"], "HOLD_NOT_IDENTIFIABLE")
        self.assertFalse(stale["receipt_accepted"])
        self.assertEqual(correlated["decision"], "HOLD_NOT_IDENTIFIABLE")
        self.assertFalse(correlated["receipt_accepted"])

    def test_external_mutation_invalidates_cached_prediction_generation(self):
        case = self.result["cases"]["external_mutation_generation"]
        self.assertEqual(case["decision"], "HOLD_STALE_GENERATION")
        self.assertFalse(case["cached_prediction_reused"])

    def test_equal_vector_does_not_certify_cross_route_hard_labels(self):
        case = self.result["cases"]["route_hard_label_mismatch"]
        self.assertTrue(case["prediction_vector_equal"])
        self.assertEqual(case["route_equivalence"], "UNKNOWN_OR_DIFFERENT")
        self.assertFalse(case["route_equivalence_claim"])

    def test_raw_only_independent_auditor_accepts_frozen_case_deck(self):
        result = audit.audit(self.result)
        self.assertEqual(result["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["errors"], [])

    def test_auditor_rejects_silent_effect_merge_mutation(self):
        mutated = candidate.run()
        mutated["cases"]["silent_effect_alias"]["merge_authorized"] = True
        result = audit.audit(mutated)
        self.assertEqual(result["disposition"], "FAIL_AUDIT")
        self.assertTrue(result["errors"])

    def test_auditor_rejects_route_equivalence_overclaim(self):
        mutated = candidate.run()
        mutated["cases"]["route_hard_label_mismatch"]["route_equivalence_claim"] = True
        mutated["cases"]["route_hard_label_mismatch"]["route_equivalence"] = "EQUIVALENT"
        result = audit.audit(mutated)
        self.assertEqual(result["disposition"], "FAIL_AUDIT")

    def test_auditor_rejects_missing_case(self):
        mutated = candidate.run()
        del mutated["cases"]["stale_receipt"]
        result = audit.audit(mutated)
        self.assertEqual(result["disposition"], "FAIL_AUDIT")

    def test_candidate_enumerates_every_permitted_test_prefix_to_fixed_horizon(self):
        case = self.result["cases"]["silent_effect_alias"]
        self.assertEqual(case["enumerated_sequence_count"], 6)
        self.assertEqual(len(case["test_sequences"]), 6)
        self.assertEqual(self.result["cases"]["delayed_beyond_horizon"]["sequence_count"], 2)

    def test_auditor_reconstructs_sequence_outputs_from_independent_oracle(self):
        result = audit.audit(self.result)
        self.assertGreaterEqual(result["oracle_transitions_replayed"], 20)
        self.assertEqual(result["oracle_mismatches"], [])

    def test_auditor_rejects_candidate_that_drops_an_enumerated_sequence(self):
        mutated = candidate.run()
        mutated["cases"]["silent_effect_alias"]["test_sequences"].pop()
        result = audit.audit(mutated)
        self.assertEqual(result["disposition"], "FAIL_AUDIT")

    def test_auditor_checks_merge_against_independent_safe_action_oracle(self):
        mutated = candidate.run()
        mutated["cases"]["null_same_safe_continuation"]["merge_authorized"] = False
        result = audit.audit(mutated)
        self.assertEqual(result["disposition"], "FAIL_AUDIT")


if __name__ == "__main__":
    unittest.main()
