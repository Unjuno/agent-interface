import unittest

import fixtures
from feedback_necessity import analyze_case, audit_result, run_candidate


class FeedbackNecessityTests(unittest.TestCase):
    def test_persistence_receipt_is_minimum_for_incompatible_safe_progress(self):
        result = analyze_case(fixtures.positive_case())
        self.assertEqual(result["decision"], "PASS_METHOD_SCOPED")
        self.assertEqual(result["minimum_exchanges"], 1)
        self.assertEqual(result["zero_exchange_witness"]["common_safe_actions"], [])

    def test_common_safe_progress_prevents_false_lower_bound(self):
        result = analyze_case(fixtures.null_case())
        self.assertEqual(result["decision"], "PASS_NULL_NO_LOWER_BOUND")
        self.assertEqual(result["minimum_exchanges"], 0)
        self.assertEqual(result["zero_exchange_witness"]["common_safe_actions"], ["inspect_again"])

    def test_undeclared_state_leak_is_rejected(self):
        case = fixtures.positive_case()
        case["channels"].append({"id": "hidden_oracle", "declared": False, "values": {"persisted": "yes", "blocked": "no"}})
        with self.assertRaisesRegex(ValueError, "undeclared"):
            analyze_case(case)

    def test_stale_receipt_cannot_satisfy_fresh_feedback_gate(self):
        case = fixtures.positive_case()
        receipt = next(channel for channel in case["channels"] if channel["id"] == "persistence_receipt")
        receipt["fresh"] = False
        result = analyze_case(case)
        self.assertIsNone(result["minimum_exchanges"])
        self.assertEqual(result["decision"], "HOLD_NO_FRESH_DISTINGUISHING_CHANNEL")

    def test_removing_distinguishing_receipt_leaves_positive_case_unresolved(self):
        case = fixtures.positive_case()
        case["channels"] = [channel for channel in case["channels"] if channel["id"] != "persistence_receipt"]
        result = analyze_case(case)
        self.assertIsNone(result["minimum_exchanges"])
        self.assertEqual(result["decision"], "HOLD_NO_FRESH_DISTINGUISHING_CHANNEL")

    def test_independent_auditor_rejects_falsified_zero_lower_bound(self):
        case = fixtures.positive_case()
        result = run_candidate([case])
        result["results"][0]["minimum_exchanges"] = 0
        result["results"][0]["decision"] = "PASS_METHOD_SCOPED"
        audit = audit_result([case], result)
        self.assertEqual(audit["status"], "FAIL_RAW_AUDIT")
        self.assertIn("minimum_exchanges", audit["errors"])

    def test_independent_oracle_rejects_forbidden_effect_relabelled_safe(self):
        case = fixtures.positive_case()
        case["worlds"][1]["safe_progress_actions"].append("claim_complete")
        audit = audit_result([case], run_candidate([case]))
        self.assertEqual(audit["status"], "FAIL_RAW_AUDIT")
        self.assertIn("oracle_action_mismatch:save-modal-positive:blocked", audit["errors"])


if __name__ == "__main__":
    unittest.main()
