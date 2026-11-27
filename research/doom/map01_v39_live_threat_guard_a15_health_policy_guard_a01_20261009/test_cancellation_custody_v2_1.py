import unittest

from audit_cancellation_custody_v2_1 import build_result


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


if __name__ == "__main__":
    unittest.main()
