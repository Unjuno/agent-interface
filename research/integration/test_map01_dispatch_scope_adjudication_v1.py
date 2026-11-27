import unittest

from research.integration.map01_dispatch_scope_adjudication_v1 import (
    adjudicate_dispatch_scope,
)


def public_row():
    operation_id = "a" * 32
    generation = "b" * 64
    attempts = [
        {"domain": "key_up", "outcome": "returned",
         "sendinput_call_started": True, "sendinput_return_count": 1,
         "sendinput_error_type": None},
        {"domain": "button_up", "outcome": "returned",
         "sendinput_call_started": True, "sendinput_return_count": 1,
         "sendinput_error_type": None},
    ]
    recovery = {
        "status": "unknown", "release_confirmed": False,
        "operation_id": operation_id, "target_generation": generation,
        "completion_readback_outcome": "not_attempted",
        "late_input_horizon_ns": 0,
        "recovery_release_attempts": attempts,
        "task_success": None, "replay_allowed": False,
    }
    return {
        "call_id": "c" * 32, "input_dispatched": False,
        "operation_invoked": False, "task_success": None,
        "replay_allowed": False,
        "action": {"operation_id": operation_id,
            "target_generation": generation, "status": "unknown",
            "input_dispatched": None, "release_confirmed": False,
            "task_success": None, "replay_allowed": False},
        "cancellation": {"automatic_completion_recovery": True,
            "status": "unknown", "release_confirmed": False,
            "action_operation_id": operation_id,
            "target_generation": generation,
            "replay_allowed": False, "result": recovery},
    }


class DispatchScopeAdjudicationTests(unittest.TestCase):
    def test_no_dispatch_and_unverified_recovery_stay_separate(self):
        result = adjudicate_dispatch_scope(public_row())
        self.assertEqual(result["classification"],
                         "NO_TASK_DISPATCH_RECOVERY_UNVERIFIED")
        self.assertEqual(result["recovery_release_attempts_returned"],
                         ["button_up", "key_up"])
        self.assertFalse(result["release_confirmed"])
        self.assertEqual(result["late_input_horizon_ns"], 0)
        self.assertIsNone(result["task_success"])
        self.assertFalse(result["replay_allowed"])

    def test_conflicting_nested_dispatch_claim_fails_closed(self):
        row = public_row()
        row["action"]["input_dispatched"] = True
        result = adjudicate_dispatch_scope(row)
        self.assertEqual(result["classification"], "UNCLASSIFIED")
        self.assertIn("source_dispatch_claim_not_unknown", result["errors"])
        self.assertFalse(result["replay_allowed"])

    def test_returned_sendinput_without_readback_is_not_release_confirmation(self):
        row = public_row()
        row["cancellation"]["result"]["completion_readback_outcome"] = "verified"
        result = adjudicate_dispatch_scope(row)
        self.assertEqual(result["classification"], "UNCLASSIFIED")
        self.assertIn("completion_readback_scope_mismatch", result["errors"])
        self.assertEqual(result["release_attempts_returned"],
                         ["button_up", "key_up"])

    def test_recovery_success_cannot_be_projected_as_pre_task_stop(self):
        row = public_row()
        row["cancellation"]["status"] = "recovered"
        row["cancellation"]["release_confirmed"] = True
        row["cancellation"]["result"]["status"] = "recovered"
        row["cancellation"]["result"]["release_confirmed"] = True
        result = adjudicate_dispatch_scope(row)
        self.assertEqual(result["classification"], "UNCLASSIFIED")
        self.assertIn("cancellation_not_unknown_unreleased", result["errors"])

    def test_non_object_is_unclassified(self):
        self.assertEqual(adjudicate_dispatch_scope(None), {
            "classification": "UNCLASSIFIED", "errors": ["row_not_object"]})


if __name__ == "__main__":
    unittest.main()
