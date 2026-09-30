import unittest

from .model import POLICIES, SCENARIOS, all_traces, summarize, trace


class FeedbackConstraintTests(unittest.TestCase):
    def test_matrix_is_complete(self):
        rows = all_traces()
        self.assertEqual(len(rows), len(POLICIES) * len(SCENARIOS))
        self.assertEqual(len({(r["policy"], r["scenario"]) for r in rows}), 20)

    def test_local_gates_miss_lost_and_stale_feedback(self):
        self.assertTrue(trace("LOCAL_GATES_ONLY", "pass_delivery_lost")["hazardous_admission"])
        self.assertTrue(trace("LOCAL_GATES_ONLY", "stale_prior_pass_acknowledged")["hazardous_admission"])

    def test_feedback_monitor_blocks_both_without_false_blocking_current_pass(self):
        for scenario in ("pass_delivery_lost", "stale_prior_pass_acknowledged"):
            row = trace("STPA_PLUS_FEEDBACK_MONITORS", scenario)
            self.assertFalse(row["admitted"])
            self.assertEqual(row["reason"], "FEEDBACK_NOT_CURRENTLY_ACKNOWLEDGED")
        self.assertTrue(trace("STPA_PLUS_FEEDBACK_MONITORS", "current_pass_acknowledged")["admitted"])

    def test_model_only_documents_but_does_not_enforce(self):
        self.assertTrue(trace("LOCAL_GATES_ONLY", "pass_delivery_lost")["admitted"])
        self.assertTrue(trace("STPA_MODEL_ONLY", "pass_delivery_lost")["admitted"])

    def test_sequence_match_is_distinct_from_delivered_ack(self):
        row = trace("STPA_PLUS_FEEDBACK_MONITORS", "pass_delivery_lost")
        self.assertTrue(row["sequence_matches"])
        self.assertFalse(row["feedback_delivered"])
        self.assertFalse(row["admitted"])

    def test_unmapped_and_reject_controls_fail_closed(self):
        self.assertFalse(trace("FAIL_CLOSED_UNMAPPED", "unmapped_action_path")["admitted"])
        self.assertFalse(trace("STPA_PLUS_FEEDBACK_MONITORS", "current_reject_delivered")["admitted"])

    def test_frozen_decision_rule_passes_only_fixture(self):
        self.assertEqual(summarize(all_traces())["status"], "PASS_FEEDBACK_CONSTRAINT_SCOPED")


if __name__ == "__main__":
    unittest.main()
