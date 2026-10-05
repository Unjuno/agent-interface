import unittest
import json
import tempfile
from pathlib import Path

from .audit_usage_qualification import (
    count_response_level_usage_records,
    qualify_usage,
)


def decision(turn_id, status, usage=None):
    return {
        "iteration": 0,
        "usage": usage,
        "final_action_admission": {
            "planner_terminal": {"turn_id": turn_id, "status": status}
        },
    }


def notification(turn_id, usage, thread_id="thread-1"):
    return {
        "method": "thread/tokenUsage/updated",
        "params": {"threadId": thread_id, "turnId": turn_id,
                    "tokenUsage": usage},
    }


def snapshot(total_input, last_input):
    return {
        "total": {"inputTokens": total_input, "outputTokens": 4},
        "last": {"inputTokens": last_input, "outputTokens": 4},
        "modelContextWindow": 258400,
    }


class UsageQualificationTests(unittest.TestCase):
    def test_interrupted_repeated_snapshot_is_not_added_or_called_zero(self):
        completed = snapshot(10, 10)
        interrupted = snapshot(10, 10)
        completed_2 = snapshot(22, 12)
        report = {
            "model_session_ids": ["thread-1"],
            "decisions": [
                decision("t0", "completed", completed),
                decision("t1", "interrupted", interrupted),
                decision("t2", "completed", completed_2),
            ],
        }
        rows = [notification("t0", completed),
                notification("t1", interrupted),
                notification("t2", completed_2)]

        result = qualify_usage(report, rows, response_level_usage_record_count=0)

        self.assertEqual(result["completed_turn_last_snapshot_sum"],
                         {"inputTokens": 22, "outputTokens": 8})
        self.assertEqual(result["interrupted_turn_ids"], ["t1"])
        self.assertEqual(result["interrupted_incremental_usage"], "UNKNOWN")
        self.assertEqual(result["full_attempt_usage"], "NOT_ESTABLISHED")
        self.assertEqual(result["response_level_usage_record_count"], 0)
        self.assertEqual(result["turns"][1]["snapshot_repeats_previous_completed"],
                         True)

    def test_missing_turn_snapshot_is_unknown_not_zero(self):
        report = {"model_session_ids": ["thread-1"],
                  "decisions": [decision("t0", "interrupted")]}
        result = qualify_usage(report, [], response_level_usage_record_count=0)

        self.assertEqual(result["missing_snapshot_turn_ids"], ["t0"])
        self.assertEqual(result["interrupted_incremental_usage"], "UNKNOWN")
        self.assertIsNone(result["completed_turn_last_snapshot_sum"])

    def test_mismatch_between_report_and_latest_notification_is_not_a_pass(self):
        reported = snapshot(10, 10)
        emitted = snapshot(11, 11)
        report = {"model_session_ids": ["thread-1"],
                  "decisions": [decision("t0", "completed", reported)]}

        result = qualify_usage(report, [notification("t0", emitted)],
                               response_level_usage_record_count=0)

        self.assertEqual(result["report_snapshot_consistency"], "MISMATCH")
        self.assertEqual(result["disposition"], "HOLD_USAGE_SNAPSHOT_MISMATCH")

    def test_only_matching_thread_and_latest_notification_are_used(self):
        earlier = snapshot(10, 10)
        latest = snapshot(14, 4)
        report = {"model_session_ids": ["thread-1"],
                  "decisions": [decision("t0", "completed", latest)]}
        rows = [notification("t0", snapshot(99, 99), thread_id="other-thread"),
                notification("t0", earlier), notification("t0", latest)]

        result = qualify_usage(report, rows, response_level_usage_record_count=0)

        self.assertEqual(result["foreign_thread_notification_count"], 1)
        self.assertEqual(result["turns"][0]["notification_count"], 2)
        self.assertEqual(result["turns"][0]["report_usage_matches_latest_notification"],
                         True)
        self.assertEqual(result["completed_turn_last_snapshot_sum"],
                         {"inputTokens": 4, "outputTokens": 4})

    def test_response_level_records_are_reported_without_claiming_completeness(self):
        usage = snapshot(10, 10)
        report = {"model_session_ids": ["thread-1"],
                  "decisions": [decision("t0", "completed", usage)]}
        result = qualify_usage(report, [notification("t0", usage)],
                               response_level_usage_record_count=2)

        self.assertEqual(result["response_level_usage_record_count"], 2)
        self.assertEqual(result["full_attempt_usage"], "NOT_ESTABLISHED")

    def test_malformed_usage_notification_holds_instead_of_disappearing(self):
        usage = snapshot(10, 10)
        report = {"model_session_ids": ["thread-1"],
                  "decisions": [decision("t0", "completed", usage)]}
        rows = [notification("t0", usage),
                {"method": "thread/tokenUsage/updated", "params": {"turnId": "t0"}}]

        result = qualify_usage(report, rows, response_level_usage_record_count=0)

        self.assertEqual(result["malformed_usage_notification_count"], 1)
        self.assertEqual(result["disposition"], "HOLD_USAGE_SNAPSHOT_MISMATCH")

    def test_response_level_record_scan_recognizes_protocol_field_spellings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "record.json").write_text(json.dumps({
                "usage": {"input_tokens": 3},
                "turn_token_usage": {"total_tokens": 3},
                "thread_token_usage": {"total_tokens": 4},
            }), encoding="utf-8")
            rows = [
                {"type": "TokenUsageRecord", "usage": {"input_tokens": 1}},
                {"records": [{"type": "TokenUsageRecord"},
                             {"type": "TokenUsageRecord"}]},
            ]
            (root / "record.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

            self.assertEqual(count_response_level_usage_records(root), 4)


if __name__ == "__main__":
    unittest.main()
