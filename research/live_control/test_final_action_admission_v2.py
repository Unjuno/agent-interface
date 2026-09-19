from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from action_validity_admission_v1 import (
    CONTRACT_FORMAT, SNAPSHOT_FORMAT, action_fingerprint,
    evaluate_action_validity)
from final_action_admission_v2 import (
    decide_final_admission, record_action_validity,
    record_controller_no_input, record_executor_admission,
    record_post_admission_revocation)


ACTION = [{"action": "fire", "extent": "pulse"}]
BINDING = {"focus": 1, "surface": 1, "geometry": [0, 0, 640, 480]}


def turn(status="completed", eligible=True, observed=10):
    return {"turn_id": "turn", "status": status, "answer_eligible": eligible,
            "terminal_observed_ns": observed}


def hard(observed=20):
    return {"outcome_evaluated_ns": observed, "outcome": {
        "status": "HARD_INVALIDATED", "reason": "below_hard_minimum",
        "requires_new_decision": True, "grants_input_authority": False}}


def validity(valid=True, observed=12):
    contract = {"format": CONTRACT_FORMAT,
                "action_fingerprint": action_fingerprint(ACTION),
                "source": {"sequence": 1, "capture_ns": 1,
                           "binding": BINDING,
                           "signals": {"health": {"status": "observed",
                                                   "value": 100}}},
                "max_current_age_ms": 500,
                "predicates": [{"signal_id": "health", "operator": "minimum",
                                "value": 90}]}
    snapshot = {"format": SNAPSHOT_FORMAT, "sequence": 2, "capture_ns": 10,
                "binding": BINDING,
                "signals": {"health": {"status": "observed",
                                        "value": 100 if valid else 80}}}
    return evaluate_action_validity(ACTION, contract, snapshot, observed)


class FinalActionAdmissionV2Tests(unittest.TestCase):
    def test_clean_path_requires_validity_then_acceptance(self):
        initial = decide_final_admission(turn(), None, 11)
        self.assertEqual(initial["status"], "READY_FOR_ACTION_VALIDITY")
        ready = record_action_validity(initial, ACTION, validity())
        self.assertEqual(ready["status"], "READY_FOR_FRESH_EXECUTOR_ADMISSION")
        admitted = record_executor_admission(
            ready, {"event": "accepted", "id": "primary", "accepted_ns": 13})
        self.assertEqual(admitted["status"], "INPUT_ADMITTED")
        self.assertTrue(admitted["input_authority_admitted"])

    def test_invalid_current_action_has_zero_admission(self):
        initial = decide_final_admission(turn(), None, 11)
        rejected = record_action_validity(initial, ACTION, validity(False))
        self.assertEqual(rejected["status"], "REJECTED_ACTION_NOT_CURRENT")
        self.assertIsNone(rejected["executor_admission"])
        with self.assertRaises(ValueError):
            record_executor_admission(
                rejected, {"event": "accepted", "id": "primary", "accepted_ns": 13})

    def test_policy_and_planner_rejections_never_reach_validity(self):
        policy = decide_final_admission(turn(observed=10), hard(20), 21)
        planner = decide_final_admission(
            turn(status="interrupted", eligible=False), None, 11)
        self.assertEqual(policy["status"], "REJECTED_POLICY_INVALIDATED")
        self.assertEqual(planner["status"], "REJECTED_PLANNER_INELIGIBLE")
        for receipt in (policy, planner):
            with self.assertRaises(ValueError):
                record_action_validity(receipt, ACTION, validity(observed=22))

    def test_controller_no_input_paths_close_before_validity(self):
        ready = decide_final_admission(turn(), None, 11)
        self.assertEqual(record_controller_no_input(
            ready, "terminal_model_state")["status"], "NO_INPUT_TERMINAL_STATE")
        self.assertEqual(record_controller_no_input(
            ready, "controller_validation_failed")["status"],
            "REJECTED_CONTROLLER_VALIDATION")

    def test_later_revocation_keeps_historical_acceptance(self):
        initial = decide_final_admission(turn(), None, 11)
        ready = record_action_validity(initial, ACTION, validity())
        admitted = record_executor_admission(
            ready, {"event": "accepted", "id": "primary", "accepted_ns": 13})
        revoked = record_post_admission_revocation(admitted, hard(14), 15)
        self.assertEqual(revoked["status"], "REVOKED_POLICY_INVALIDATED")
        self.assertFalse(revoked["input_authority_admitted"])
        self.assertEqual(revoked["executor_admission"], admitted["executor_admission"])

    def test_inconsistent_early_or_forged_validity_fails_closed(self):
        ready = decide_final_admission(turn(), None, 11)
        with self.assertRaises(ValueError):
            record_action_validity(ready, ACTION, validity(observed=10))
        forged = validity(); forged["grants_input_authority"] = True
        with self.assertRaises(ValueError):
            record_action_validity(ready, ACTION, forged)
        forged = validity(); forged["checks"][0]["observed"] = 999
        with self.assertRaises(ValueError):
            record_action_validity(ready, ACTION, forged)
        with self.assertRaises(ValueError):
            record_action_validity(
                ready, [{"action": "forward", "extent": "pulse"}], validity())


if __name__ == "__main__":
    unittest.main()
