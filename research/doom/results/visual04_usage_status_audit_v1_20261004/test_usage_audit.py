import unittest

from usage_audit import audit_usage


def terminal(turn_id, status):
    return {
        "iteration": len(turn_id),
        "final_action_admission": {
            "planner_terminal": {"turn_id": turn_id, "status": status}
        },
    }


def notification(turn_id, input_tokens, output_tokens):
    usage = {
        "totalTokens": input_tokens + output_tokens,
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
    }
    return {
        "method": "thread/tokenUsage/updated",
        "params": {
            "turnId": turn_id,
            "tokenUsage": {"total": usage, "last": usage},
        },
    }


class UsageAuditTests(unittest.TestCase):
    def test_interrupted_repeated_snapshot_is_not_counted_as_a_turn_delta(self):
        report = {"decisions": [terminal("done", "completed"), terminal("stop", "interrupted")]}
        notifications = [notification("done", 100, 10), notification("stop", 100, 10)]

        result = audit_usage(report, notifications)

        self.assertEqual(result["completed_turn_last_snapshot_sum"], {"inputTokens": 100, "outputTokens": 10})
        self.assertEqual(result["unknown_interrupted_turns"], ["stop"])
        self.assertTrue(result["interrupted_usage_interpretation"].startswith("UNKNOWN;"))

    def test_interrupted_changed_snapshot_still_has_unknown_increment(self):
        report = {"decisions": [terminal("done", "completed"), terminal("stop", "interrupted")]}
        notifications = [notification("done", 100, 10), notification("stop", 500, 50)]

        result = audit_usage(report, notifications)

        self.assertEqual(result["unknown_interrupted_turns"], ["stop"])
        self.assertEqual(result["completed_turn_last_snapshot_sum"], {"inputTokens": 100, "outputTokens": 10})


if __name__ == "__main__":
    unittest.main()
