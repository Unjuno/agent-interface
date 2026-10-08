import unittest

from audit_cancellation_custody_v2_1 import build_result
from audit_live import reconcile_cancelled_cover_custody


class CancellationCustodyV21Tests(unittest.TestCase):
    def test_missing_failure_receipt_is_normal_and_does_not_raise(self):
        audit = {"status": "FAIL", "formal_pass": False,
                 "counts": {"hard_health_guard_exposures": 0,
                            "useful_events_during_model_wait": 0}}
        result = build_result([], audit, {"player_dead": False}, None)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["controller_failure_receipt_present"])
        self.assertIsNone(result["primary_runtime_error"])
        self.assertEqual(result["original_audit_status_preserved"], "FAIL")

    def test_present_failure_receipt_is_preserved_as_stop(self):
        failure = {"primary_error_type": "RuntimeError", "failed_stage": "input",
                   "input_releases_verified_empty": True}
        result = build_result([], {"status": "PASS", "formal_pass": True},
                              {"player_dead": False}, failure)
        self.assertEqual(result["status"], "STOP")
        self.assertTrue(result["controller_failure_receipt_present"])
        self.assertEqual(result["primary_runtime_error"],
                         {"type": "RuntimeError", "stage": "input"})

    def test_uncustodied_cancellation_remains_fail_even_without_receipt(self):
        events = [{"event": "cancel_requested", "id": "x", "matched": True}]
        result = build_result(events, {"status": "PASS", "formal_pass": True},
                              {"player_dead": False}, None)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["custody"]["unaccounted_cancel_ids"], ["x"])

    def test_duplicate_cancel_identity_fails_closed(self):
        receipt = {"verified": True, "keys_down": [], "buttons_down": [],
                   "keys_unknown": []}
        events = [
            {"event": "cancel_requested", "id": "dup", "matched": True},
            {"event": "cancel_requested", "id": "dup", "matched": True},
            {"event": "terminal", "id": "dup", "status": "cancelled",
             "release": receipt},
        ]
        result = build_result(events, {"status": "PASS", "formal_pass": True},
                              {"player_dead": False}, None)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["custody"]["duplicate_cancel_ids"], ["dup"])

    def test_duplicate_terminal_identity_fails_closed(self):
        receipt = {"verified": True, "keys_down": [], "buttons_down": [],
                   "keys_unknown": []}
        events = [
            {"event": "cancel_requested", "id": "dup", "matched": True},
            {"event": "terminal", "id": "dup", "status": "cancelled",
             "release": receipt},
            {"event": "terminal", "id": "dup", "status": "cancelled",
             "release": receipt},
        ]
        result = build_result(events, {"status": "PASS", "formal_pass": True},
                              {"player_dead": False}, None)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["custody"]["duplicate_terminal_ids"], ["dup"])

    def test_frozen_auditor_accepts_no_lease_cancel_with_empty_terminal(self):
        events = [
            {"event": "cancel_requested", "id": "no-lease", "matched": True},
            {"event": "terminal", "id": "no-lease", "status": "cancelled",
             "release": {"verified": True, "keys_down": [],
                         "buttons_down": [], "keys_unknown": []}},
        ]
        result = reconcile_cancelled_cover_custody(events)
        self.assertTrue(result["all_cancellations_custodied"])
        self.assertEqual(result["no_active_lease_ids"], ["no-lease"])

    def test_frozen_auditor_rejects_active_lease_without_owner_release(self):
        token = "lease-1"
        events = [
            {"event": "input_admission", "id": "active", "intent_token": token},
            {"event": "cancel_requested", "id": "active", "matched": True},
            {"event": "terminal", "id": "active", "status": "cancelled",
             "interruption": {"intent_token": token},
             "release": {"verified": True, "keys_down": [],
                         "buttons_down": [], "keys_unknown": []}},
        ]
        result = reconcile_cancelled_cover_custody(events)
        self.assertFalse(result["all_cancellations_custodied"])
        self.assertEqual(result["unaccounted_cancel_ids"], ["active"])


if __name__ == "__main__":
    unittest.main()
