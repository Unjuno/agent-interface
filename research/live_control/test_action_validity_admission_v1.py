import copy
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from action_validity_admission_v1 import (
    CONTRACT_FORMAT, SNAPSHOT_FORMAT, action_fingerprint,
    evaluate_action_validity)


ACTION = [{"action": "retreat_fire", "extent": "short"}]
BINDING = {"focus": 1, "surface": 1, "geometry": [0, 0, 640, 480]}


def contract():
    return {"format": CONTRACT_FORMAT, "action_fingerprint": action_fingerprint(ACTION),
            "source": {"sequence": 10, "capture_ns": 1_000_000_000,
                       "binding": BINDING,
                       "signals": {"health": {"status": "observed", "value": 85},
                                   "enemy_visible": {"status": "observed", "value": True}}},
            "max_current_age_ms": 250,
            "predicates": [
                {"signal_id": "health", "operator": "minimum", "value": 45},
                {"signal_id": "health", "operator": "max_decrease_from_source", "value": 8},
                {"signal_id": "enemy_visible", "operator": "equals", "value": True}]}


def snapshot():
    return {"format": SNAPSHOT_FORMAT, "sequence": 20,
            "capture_ns": 1_100_000_000, "binding": BINDING,
            "signals": {"health": {"status": "observed", "value": 79},
                        "enemy_visible": {"status": "observed", "value": True}}}


class ActionValidityAdmissionTests(unittest.TestCase):
    def test_bounded_change_preserves_eligibility_without_authority(self):
        result = evaluate_action_validity(ACTION, contract(), snapshot(), 1_101_000_000)
        self.assertEqual(result["status"], "VALID_CURRENT")
        self.assertTrue(result["action_may_proceed_to_executor_admission"])
        self.assertFalse(result["grants_input_authority"])

    def test_predicate_breach_rejects(self):
        current = snapshot()
        current["signals"]["health"]["value"] = 76
        result = evaluate_action_validity(ACTION, contract(), current, 1_101_000_000)
        self.assertEqual(result["status"], "REJECTED_PREDICATE")
        self.assertTrue(result["requires_new_decision"])

    def test_unobservable_required_signal_fails_closed(self):
        current = snapshot()
        current["signals"]["enemy_visible"] = {"status": "unknown", "value": None}
        result = evaluate_action_validity(ACTION, contract(), current, 1_101_000_000)
        self.assertEqual(result["status"], "REJECTED_SIGNAL_UNKNOWN")

    def test_stale_binding_sequence_and_action_are_distinct(self):
        stale = evaluate_action_validity(ACTION, contract(), snapshot(), 1_400_000_001)
        self.assertEqual(stale["status"], "REJECTED_STALE")
        moved = snapshot(); moved["binding"] = {**BINDING, "focus": 2}
        self.assertEqual(evaluate_action_validity(
            ACTION, contract(), moved, 1_101_000_000)["status"], "REJECTED_STATE_BINDING")
        older = snapshot(); older["sequence"] = 9
        self.assertEqual(evaluate_action_validity(
            ACTION, contract(), older, 1_101_000_000)["status"], "REJECTED_SEQUENCE")
        self.assertEqual(evaluate_action_validity(
            [{"action": "fire", "extent": "pulse"}], contract(), snapshot(),
            1_101_000_000)["status"], "REJECTED_ACTION_BINDING")

    def test_malformed_or_empty_contract_is_refused(self):
        empty = contract(); empty["predicates"] = []
        with self.assertRaises(ValueError):
            evaluate_action_validity(ACTION, empty, snapshot(), 1_101_000_000)
        duplicate = contract()
        duplicate["predicates"].append(copy.deepcopy(duplicate["predicates"][0]))
        with self.assertRaises(ValueError):
            evaluate_action_validity(ACTION, duplicate, snapshot(), 1_101_000_000)


if __name__ == "__main__":
    unittest.main()
