import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("candidate", HERE / "analyze_map01_direct_retained_input_v1.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class Tests(unittest.TestCase):
    def test_direct_transition_is_measurable(self):
        events = [
            {"event": "input_admission", "intent_token": "t", "key": "Up",
             "admitted_ns": 100_000_000, "input_ack_ns": 110_000_000},
            {"event": "input_release_transition", "intent_token": "t", "operation": "up",
             "key": "Up", "release_call_started_ns": 410_000_000,
             "release_call_returned_ns": 420_000_000, "owner_transition_verified": True},
        ]
        result = candidate.analyze(events)
        self.assertTrue(result["measurement_ready"])
        self.assertEqual(result["hold_count"], 1)
        self.assertEqual(result["holds"][0]["retained_lower_ms"], 300.0)
        self.assertEqual(result["holds"][0]["retained_upper_ms"], 320.0)
        self.assertEqual(result["holds"][0]["censor_width_ms"], 20.0)

    def test_current_schema_proxy_trace_is_rejected(self):
        events = [
            {"event": "step_started", "id": "x", "step": 0, "operation": "hold", "issued_ns": 1},
            {"event": "input_admission", "key": "Up", "admitted_ns": 2, "input_ack_ns": 3},
            {"event": "observation", "id": "x", "step": 0, "capture_ns": 100},
            {"event": "step_completed", "id": "x", "step": 0, "completed_ns": 200},
            {"event": "terminal", "id": "x", "status": "completed", "terminal_ns": 300},
        ]
        result = candidate.analyze(events)
        self.assertFalse(result["measurement_ready"])
        self.assertEqual(result["unmatched_admission_count"], 1)

    def test_unverified_release_is_rejected(self):
        events = [
            {"event": "input_admission", "intent_token": "t", "key": "Up",
             "admitted_ns": 1, "input_ack_ns": 2},
            {"event": "input_release_transition", "intent_token": "t", "operation": "up",
             "key": "Up", "release_call_started_ns": 3, "release_call_returned_ns": 4,
             "owner_transition_verified": False},
        ]
        result = candidate.analyze(events)
        self.assertFalse(result["measurement_ready"])
        self.assertEqual(result["invalid_release_count"], 1)


if __name__ == "__main__":
    unittest.main()
