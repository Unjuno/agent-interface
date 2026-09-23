import copy
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from action_validity_admission_v1 import (
    CONTRACT_FORMAT, SNAPSHOT_FORMAT, action_fingerprint,
    evaluate_action_validity)
from running_action_guard_v1 import (
    ACTIVE, BETWEEN, CANCEL, COMPLETED, READY, REJECTED, REVOKED,
    RunningActionGuard)


BINDING = {"focus": 7, "surface": 8, "geometry": [0, 0, 640, 480]}
ACTION = [{"action": "advance_fire", "extent": "long"}]


def snapshot(sequence, capture_ns, health=90, ammo=12, binding=None):
    return {"format": SNAPSHOT_FORMAT, "sequence": sequence,
            "capture_ns": capture_ns, "binding": binding or BINDING,
            "signals": {"health": {"status": "observed", "value": health},
                        "ammo": {"status": "observed", "value": ammo}}}


def contract():
    return {"format": CONTRACT_FORMAT, "action_fingerprint": action_fingerprint(ACTION),
            "source": {"sequence": 1, "capture_ns": 100, "binding": BINDING,
                       "signals": {"health": {"status": "observed", "value": 90},
                                   "ammo": {"status": "observed", "value": 12}}},
            "max_current_age_ms": 500,
            "predicates": [
                {"signal_id": "health", "operator": "minimum", "value": 50},
                {"signal_id": "health", "operator": "max_decrease_from_source", "value": 8},
                {"signal_id": "ammo", "operator": "minimum", "value": 1}]}


def guard():
    spec = contract()
    initial = evaluate_action_validity(ACTION, spec, snapshot(2, 200), 201)
    return RunningActionGuard(ACTION, spec, initial)


def accepted(identifier="p1", when=210):
    return {"event": "accepted", "id": identifier, "accepted_ns": when}


def terminal(identifier, status, when):
    return {"event": "terminal", "id": identifier, "status": status,
            "terminal_ns": when,
            "release": {"verified": True, "keys_down": [], "buttons_down": [],
                        "verified_ns": when - 1}}


class RunningActionGuardTests(unittest.TestCase):
    def test_valid_running_observation_preserves_active_authority(self):
        value = guard(); value.admit_program(accepted())
        receipt = value.check_current(snapshot(3, 300, health=84, ammo=10), 301)
        self.assertEqual(receipt["state"], ACTIVE)
        self.assertTrue(receipt["current_input_authority"])
        self.assertFalse(receipt["requires_new_decision"])
        self.assertEqual(len(receipt["validity_checks"]), 2)

    def test_health_breach_requires_cancel_and_verified_release(self):
        value = guard(); value.admit_program(accepted())
        receipt = value.check_current(snapshot(3, 300, health=81), 301)
        self.assertEqual(receipt["state"], CANCEL)
        self.assertFalse(receipt["current_input_authority"])
        self.assertTrue(receipt["physical_input_may_be_down"])
        self.assertFalse(receipt["physical_release_verified"])
        value.record_cancel_requested(
            {"event": "cancel_requested", "id": "p1", "matched": True, "requested_ns": 302})
        receipt = value.record_cancelled_terminal(terminal("p1", "cancelled", 305))
        self.assertEqual(receipt["state"], REVOKED)
        self.assertTrue(receipt["physical_release_verified"])
        self.assertEqual(receipt["program_admissions"], [accepted()])

    def test_ammo_exhaustion_invalidates_fire_action(self):
        value = guard(); value.admit_program(accepted())
        receipt = value.check_current(snapshot(3, 300, ammo=0), 301)
        self.assertEqual(receipt["state"], CANCEL)
        self.assertEqual(receipt["invalidation"]["result"]["reason"], "ammo_minimum_failed")

    def test_completed_segment_requires_fresh_check_before_next_program(self):
        value = guard(); value.admit_program(accepted())
        value.check_current(snapshot(3, 300), 301)
        receipt = value.record_completed_terminal(terminal("p1", "completed", 310), final=False)
        self.assertEqual(receipt["state"], BETWEEN)
        with self.assertRaises(ValueError):
            value.admit_program(accepted("p2", 320))
        self.assertEqual(value.check_current(snapshot(4, 315), 316)["state"], READY)
        self.assertEqual(value.admit_program(accepted("p2", 320))["state"], ACTIVE)

    def test_invalid_between_segments_rejects_without_cancel(self):
        value = guard(); value.admit_program(accepted())
        value.check_current(snapshot(3, 300), 301)
        value.record_completed_terminal(terminal("p1", "completed", 310), final=False)
        receipt = value.check_current(snapshot(4, 315, health=40), 316)
        self.assertEqual(receipt["state"], REJECTED)
        self.assertIsNone(receipt["active_program"])
        self.assertIsNone(receipt["cancellation"])

    def test_nonmonotonic_observation_fails_closed(self):
        value = guard(); value.admit_program(accepted())
        receipt = value.check_current(snapshot(2, 200), 211)
        self.assertEqual(receipt["state"], CANCEL)
        self.assertEqual(receipt["invalidation"]["kind"], "observation_order")

    def test_binding_change_requires_cancel(self):
        value = guard(); value.admit_program(accepted())
        changed = {"focus": 9, "surface": 8, "geometry": [0, 0, 640, 480]}
        receipt = value.check_current(snapshot(3, 300, binding=changed), 301)
        self.assertEqual(receipt["state"], CANCEL)
        self.assertEqual(receipt["invalidation"]["result"]["status"], "REJECTED_STATE_BINDING")

    def test_final_completion_retains_history_and_ends_authority(self):
        value = guard(); value.admit_program(accepted())
        value.check_current(snapshot(3, 300), 301)
        receipt = value.record_completed_terminal(terminal("p1", "completed", 310), final=True)
        self.assertEqual(receipt["state"], COMPLETED)
        self.assertFalse(receipt["current_input_authority"])
        self.assertEqual(len(receipt["program_terminals"]), 1)

    def test_action_can_close_after_branch_decision(self):
        value = guard(); value.admit_program(accepted())
        value.check_current(snapshot(3, 300), 301)
        value.record_completed_terminal(terminal("p1", "completed", 310), final=False)
        receipt = value.record_action_complete()
        self.assertEqual(receipt["state"], COMPLETED)
        with self.assertRaises(ValueError):
            value.record_action_complete()

    def test_mismatched_cancel_and_unverified_release_are_rejected(self):
        value = guard(); value.admit_program(accepted())
        value.check_current(snapshot(3, 300, health=81), 301)
        with self.assertRaises(ValueError):
            value.record_cancel_requested(
                {"event": "cancel_requested", "id": "wrong", "matched": True, "requested_ns": 302})
        value.record_cancel_requested(
            {"event": "cancel_requested", "id": "p1", "matched": True, "requested_ns": 302})
        bad = terminal("p1", "cancelled", 305)
        bad["release"]["keys_down"] = ["Up"]
        with self.assertRaises(ValueError):
            value.record_cancelled_terminal(bad)

    def test_forged_initial_result_is_rejected(self):
        spec = contract()
        initial = evaluate_action_validity(ACTION, spec, snapshot(2, 200), 201)
        forged = copy.deepcopy(initial); forged["checks"][0]["passed"] = False
        with self.assertRaises(ValueError):
            RunningActionGuard(ACTION, spec, forged)


if __name__ == "__main__":
    unittest.main()
