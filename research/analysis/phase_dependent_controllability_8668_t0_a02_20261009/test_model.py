"""Construction regressions for the A02 policy-specific finite plant."""
import unittest
import json

import candidate
import auditor


def schedule(phase, c=0, r=0, tie="CONTROL_FIRST", receipt="RELEASE_FIRST", retry=True):
    return {"schedule_id": "test", "request_phase": phase,
            "control_delay_transitions": c, "removal_receipt_delay_transitions": r,
            "same_frontier_order": tie, "effect_receipt_order": receipt,
            "stale_receipt_position": "NONE", "retry_requested": retry}


class ModelBoundaryTests(unittest.TestCase):
    def test_candidate_matches_independent_oracle_for_every_frozen_schedule(self):
        spec = json.loads((candidate.ROOT / "design.json").read_text())
        policies = tuple(spec["policies"])
        constructed = [{"exogenous_schedule": row,
                        "policy_outcomes": {name: candidate.simulate(row, name)
                                            for name in policies}}
                       for row in candidate.schedules(spec)]
        self.assertEqual(constructed, auditor.expected_rows(spec))

    def test_same_frontier_order_is_decisive(self):
        self.assertTrue(candidate.removal_is_confirmed("QUEUED", 1, 0, "CONTROL_FIRST"))
        self.assertFalse(candidate.removal_is_confirmed("QUEUED", 1, 0, "PLANT_FIRST"))

    def test_request_at_or_after_emission_cannot_remove(self):
        for phase in ("EMITTED", "CONSUMED"):
            self.assertFalse(candidate.removal_is_confirmed(phase, 0, 0, "CONTROL_FIRST"))

    def test_phase_refined_requires_operation_removal_confirmation(self):
        row = schedule("QUEUED", c=1, r=0, tie="PLANT_FIRST")
        outcome = candidate.simulate(row, "PHASE_REFINED")
        self.assertFalse(outcome["actual"]["removal_confirmed_before_emit"])
        self.assertTrue(outcome["actual"]["effect_committed"])
        self.assertEqual(outcome["controller"]["reported_state_at_retry"], "UNKNOWN")
        self.assertFalse(outcome["controller"]["retry_admitted"])
        self.assertFalse(outcome["controller"]["unsafe_duplicate"])

    def test_static_cancelable_counterexample_is_policy_specific(self):
        row = schedule("EMITTED", receipt="RELEASE_FIRST")
        optimistic = candidate.simulate(row, "STATIC_CANCELABLE")
        conservative = candidate.simulate(row, "STATIC_UNCONTROLLABLE")
        self.assertTrue(optimistic["actual"]["effect_committed"])
        self.assertTrue(optimistic["controller"]["false_cancel_claim"])
        self.assertTrue(optimistic["controller"]["unsafe_duplicate"])
        self.assertFalse(conservative["actual"]["cancel_requested"])

    def test_late_cancel_command_is_not_available_at_retry_cut(self):
        row = schedule("CONSUMED", c=1, r=0)
        outcome = candidate.simulate(row, "STATIC_CANCELABLE")
        self.assertFalse(outcome["actual"]["cancel_command_delivered_by_retry_decision"])
        self.assertEqual(outcome["controller"]["reported_state_at_retry"], "UNKNOWN")
        self.assertFalse(outcome["controller"]["retry_admitted"])

    def test_static_uncontrollable_misses_available_pre_emit_removal(self):
        row = schedule("PROPOSED", retry=True)
        outcome = candidate.simulate(row, "STATIC_UNCONTROLLABLE")
        self.assertTrue(outcome["controller"]["safe_cancel_missed"])

    def test_no_input_control_is_idle(self):
        row = {"schedule_id": "no-input-control", "request_phase": "NONE",
               "control_delay_transitions": 0, "removal_receipt_delay_transitions": 0,
               "same_frontier_order": "CONTROL_FIRST", "effect_receipt_order": "EFFECT_FIRST",
               "stale_receipt_position": "NONE", "retry_requested": False}
        self.assertEqual(candidate.simulate(row, "PHASE_REFINED")["controller"]["reported_state_at_retry"],
                         "IDLE")


if __name__ == "__main__":
    unittest.main()
