import json
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
from final_action_admission_v1 import (
    decide_final_admission, record_executor_admission,
    record_controller_no_input, record_post_admission_revocation)


def turn(status="completed", eligible=True, observed=20):
    return {"turn_id": "turn-1", "status": status,
            "answer_eligible": eligible, "terminal_observed_ns": observed}


def hard(observed=10):
    return {"outcome_evaluated_ns": observed, "outcome": {
        "status": "HARD_INVALIDATED", "reason": "below_hard_minimum",
        "requires_new_decision": True, "grants_input_authority": False}}


class FinalActionAdmissionTests(unittest.TestCase):
    def test_hard_before_terminal_wins(self):
        receipt = decide_final_admission(turn(observed=20), hard(observed=10), 21)
        self.assertEqual(receipt["status"], "REJECTED_POLICY_INVALIDATED")
        self.assertFalse(receipt["input_authority_admitted"])

    def test_terminal_before_hard_before_admission_also_rejects(self):
        receipt = decide_final_admission(turn(observed=10), hard(observed=20), 21)
        self.assertEqual(receipt["status"], "REJECTED_POLICY_INVALIDATED")
        with self.assertRaises(ValueError):
            record_executor_admission(
                receipt, {"event": "accepted", "id": "plan", "accepted_ns": 22})

    def test_clean_completion_requires_fresh_executor_acceptance(self):
        ready = decide_final_admission(turn(observed=10), None, 11)
        self.assertEqual(ready["status"], "READY_FOR_FRESH_EXECUTOR_ADMISSION")
        self.assertFalse(ready["input_authority_admitted"])
        admitted = record_executor_admission(
            ready, {"event": "accepted", "id": "plan", "accepted_ns": 12})
        self.assertEqual(admitted["status"], "INPUT_ADMITTED")
        self.assertTrue(admitted["input_authority_admitted"])
        self.assertFalse(admitted["grants_input_authority"])

    def test_later_hard_revokes_without_rewriting_admission(self):
        ready = decide_final_admission(turn(observed=10), None, 11)
        admitted = record_executor_admission(
            ready, {"event": "accepted", "id": "plan", "accepted_ns": 12})
        revoked = record_post_admission_revocation(admitted, hard(observed=13), 14)
        self.assertEqual(revoked["status"], "REVOKED_POLICY_INVALIDATED")
        self.assertFalse(revoked["input_authority_admitted"])
        self.assertEqual(revoked["executor_admission"], admitted["executor_admission"])

    def test_ready_can_close_as_typed_no_input(self):
        ready = decide_final_admission(turn(observed=10), None, 11)
        terminal = record_controller_no_input(ready, "terminal_model_state")
        invalid = record_controller_no_input(ready, "controller_validation_failed")
        self.assertEqual(terminal["status"], "NO_INPUT_TERMINAL_STATE")
        self.assertEqual(invalid["status"], "REJECTED_CONTROLLER_VALIDATION")
        self.assertFalse(terminal["input_authority_admitted"])
        with self.assertRaises(ValueError):
            record_controller_no_input(terminal, "terminal_model_state")

    def test_ineligible_or_malformed_boundaries_fail_closed(self):
        receipt = decide_final_admission(turn(status="interrupted", eligible=False), None, 21)
        self.assertEqual(receipt["status"], "REJECTED_PLANNER_INELIGIBLE")
        with self.assertRaises(ValueError):
            decide_final_admission(turn(), hard(observed=30), 21)
        forged = hard()
        forged["outcome"]["grants_input_authority"] = True
        with self.assertRaises(ValueError):
            decide_final_admission(turn(), forged, 21)

    def test_retained_v31_terminal_hard_race_is_typed_rejection(self):
        root = REPO / "research/doom/results/map01-soft-context-v31-live-01"
        report = json.loads((root / "report.json").read_text())
        decision = report["decisions"][0]
        protocol = [json.loads(line) for line in
                    (root / "planner-protocol.jsonl").read_text().splitlines()]
        completion = next(row for row in protocol
            if row.get("direction") == "received" and
            row.get("message", {}).get("method") == "turn/completed" and
            row["message"]["params"]["turn"]["id"] == decision["planner_turn_id"])
        terminal = {"turn_id": decision["planner_turn_id"],
                    "status": decision["planner_turn_status"],
                    "answer_eligible": decision["planner_answer_eligible"],
                    "terminal_observed_ns": completion["observed_ns"]}
        decided_ns = max(completion["observed_ns"],
                         decision["policy_invalidation"]["outcome_evaluated_ns"]) + 1
        receipt = decide_final_admission(
            terminal, decision["policy_invalidation"], decided_ns)
        self.assertEqual(receipt["status"], "REJECTED_POLICY_INVALIDATED")
        self.assertEqual(decision["planner_interrupt"]["outcome"], "already_terminal")
        self.assertTrue(decision["model_action_discarded"])
        self.assertEqual(decision["plan_terminal"], "not_admitted")


if __name__ == "__main__":
    unittest.main()
