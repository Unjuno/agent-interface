import unittest
from audit_cancellation_custody_v3 import reconcile_cancellations, classify_status


def terminal(identifier, status="cancelled"):
    return {"event": "terminal", "id": identifier, "status": status,
            "release": {"event": "owner_release", "verified": True,
                        "keys_down": [], "buttons_down": [], "keys_unknown": [],
                        "key_state_errors": [], "intent_token": None}}


class CancellationCustodyV3Tests(unittest.TestCase):
    def test_no_admission_uses_verified_empty_terminal_without_failure_receipt(self):
        events = [{"event": "cancel_requested", "id": "c0", "matched": True},
                  terminal("c0")]
        result = reconcile_cancellations(events)
        self.assertTrue(result["all_cancellations_custodied"])
        self.assertEqual(result["no_active_lease_ids"], ["c0"])

    def test_admitted_cancellation_requires_matching_owner_release(self):
        token = "lease-1"
        events = [
            {"event": "cancel_requested", "id": "c1", "matched": True},
            {"event": "input_admission", "id": "c1", "intent_token": token},
            {"event": "input_released", "id": "c1", "intent_token": token,
             "owner_release": {"event": "owner_release", "reason": "cancelled",
                               "verified": True, "keys_down": [], "buttons_down": [],
                               "keys_unknown": [], "key_state_errors": [],
                               "intent_token": token}},
            terminal("c1"),
        ]
        result = reconcile_cancellations(events)
        self.assertTrue(result["all_cancellations_custodied"])
        self.assertEqual(result["active_lease_ids"], ["c1"])

    def test_admitted_cancellation_without_matching_release_fails(self):
        events = [
            {"event": "cancel_requested", "id": "c2", "matched": True},
            {"event": "input_admission", "id": "c2", "intent_token": "lease-2"},
            terminal("c2"),
        ]
        result = reconcile_cancellations(events)
        self.assertFalse(result["all_cancellations_custodied"])
        self.assertEqual(result["unaccounted_cancel_ids"], ["c2"])

    def test_incomplete_custody_is_fail_and_complete_unexposed_gate_is_hold(self):
        safe_score = {"player_dead": False, "map_exit": False}
        unexposed = {"hard_health_guard_exposed": False,
                     "useful_feedback_during_pending_model": False,
                     "bounded_fresh_recovery_after_guard": False}
        exposed = {"hard_health_guard_exposed": True,
                   "useful_feedback_during_pending_model": True,
                   "bounded_fresh_recovery_after_guard": True}
        self.assertEqual(classify_status(False, unexposed, safe_score, None), "FAIL")
        self.assertEqual(classify_status(True, unexposed, safe_score, None), "HOLD")
        self.assertEqual(classify_status(True, exposed, safe_score, None), "PASS")
        self.assertEqual(classify_status(True, unexposed,
                                         {"player_dead": True}, None), "STOP")
        self.assertEqual(classify_status(True, unexposed,
                                         {"episode_finished": True}, None), "STOP")


if __name__ == "__main__":
    unittest.main()
