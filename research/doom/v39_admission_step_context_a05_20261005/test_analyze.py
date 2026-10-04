import unittest

from analyze import analyze


class StepContextJoinTests(unittest.TestCase):
    def test_groups_multiple_key_admissions_under_one_same_step_receipt(self):
        events = [
            {"event": "step_started", "id": "p", "step": 2, "operation": "hold"},
            {"event": "input_admission", "key": "a", "input_ack_ns": 10},
            {"event": "input_admission", "key": "space", "input_ack_ns": 20},
            {"event": "keys_held", "id": "p", "step": 2, "keys": ["a", "space"], "input_ack_ns": 30},
            {"event": "step_completed", "id": "p", "step": 2},
        ]
        result = analyze(events)
        self.assertEqual(result["counts"]["unique_same_step_receipt"], 2)
        self.assertEqual([row["same_step_receipts"][0]["event_index"] for row in result["rows"]], [3, 3])
        self.assertEqual([row["ack_gap_ns"] for row in result["rows"]], [20, 10])

    def test_cancelled_admission_does_not_join_later_same_key_step(self):
        events = [
            {"event": "step_started", "id": "old", "step": 10, "operation": "hold"},
            {"event": "input_admission", "key": "Down", "input_ack_ns": 10},
            {"event": "cancel_requested", "id": "old"},
            {"event": "terminal", "id": "old", "status": "cancelled"},
            {"event": "step_started", "id": "new", "step": 0, "operation": "hold"},
            {"event": "input_admission", "key": "Down", "input_ack_ns": 20},
            {"event": "keys_held", "id": "new", "step": 0, "keys": ["Down"], "input_ack_ns": 30},
        ]
        result = analyze(events)
        self.assertEqual(result["rows"][0]["association"], "NO_SAME_STEP_AGGREGATE_ACK")
        self.assertEqual(result["rows"][0]["step_context"]["id"], "old")
        self.assertEqual(result["rows"][1]["same_step_receipt_count"], 1)

    def test_duplicate_receipts_in_same_step_remain_ambiguous(self):
        events = [
            {"event": "step_started", "id": "p", "step": 0, "operation": "hold"},
            {"event": "input_admission", "key": "a", "input_ack_ns": 10},
            {"event": "keys_held", "id": "p", "step": 0, "keys": ["a"], "input_ack_ns": 20},
            {"event": "keys_held", "id": "p", "step": 0, "keys": ["a"], "input_ack_ns": 25},
        ]
        result = analyze(events)
        self.assertEqual(result["rows"][0]["association"], "AMBIGUOUS_SAME_STEP_AGGREGATE_ACK")

    def test_admission_after_step_completion_has_no_active_context(self):
        events = [
            {"event": "step_started", "id": "p", "step": 0, "operation": "hold"},
            {"event": "step_completed", "id": "p", "step": 0},
            {"event": "input_admission", "key": "a", "input_ack_ns": 10},
            {"event": "keys_held", "id": "p", "step": 0, "keys": ["a"], "input_ack_ns": 20},
        ]
        result = analyze(events)
        self.assertEqual(result["rows"][0]["association"], "NO_SAME_STEP_AGGREGATE_ACK")

    def test_receipt_after_matched_cancel_does_not_confirm_admission(self):
        events = [
            {"event": "step_started", "id": "p", "step": 0, "operation": "hold"},
            {"event": "input_admission", "key": "a", "input_ack_ns": 10},
            {"event": "cancel_requested", "id": "p", "matched": True},
            {"event": "keys_held", "id": "p", "step": 0, "keys": ["a"], "input_ack_ns": 20},
        ]
        result = analyze(events)
        self.assertEqual(result["rows"][0]["association"], "NO_SAME_STEP_AGGREGATE_ACK")


if __name__ == "__main__":
    unittest.main()
