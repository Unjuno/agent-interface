import importlib.util
from itertools import product
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
        self.assertEqual(result["invalid_admission_count"], 1)

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

    def test_timestamp_order_inversions_are_rejected(self):
        def pair(admitted_ns, input_ack_ns, release_start_ns, release_return_ns):
            return [
                {"event": "input_admission", "intent_token": "t", "key": "a",
                 "admitted_ns": admitted_ns, "input_ack_ns": input_ack_ns},
                {"event": "input_release_transition", "intent_token": "t", "operation": "up",
                 "key": "a", "release_call_started_ns": release_start_ns,
                 "release_call_returned_ns": release_return_ns,
                 "owner_transition_verified": True},
            ]

        cases = {
            "ack_before_admission": pair(200, 100, 300, 400),
            "release_before_ack": pair(100, 200, 150, 250),
            "release_before_admission": pair(100, 110, 50, 60),
            "release_bracket_reversed": pair(100, 110, 130, 120),
        }
        for name, events in cases.items():
            with self.subTest(name=name):
                result = candidate.analyze(events)
                self.assertFalse(result["measurement_ready"], result)
                self.assertEqual(result["hold_count"], 0, result)
                self.assertEqual(result["invalid_release_count"], 1, result)

    def test_equal_adjacent_timestamp_boundaries_are_allowed(self):
        events = [
            {"event": "input_admission", "intent_token": "t", "key": "a",
             "admitted_ns": 100, "input_ack_ns": 100},
            {"event": "input_release_transition", "intent_token": "t", "operation": "up",
             "key": "a", "release_call_started_ns": 100,
             "release_call_returned_ns": 100, "owner_transition_verified": True},
        ]
        result = candidate.analyze(events)
        self.assertTrue(result["measurement_ready"], result)
        self.assertEqual(result["holds"][0]["retained_lower_ms"], 0.0)
        self.assertEqual(result["holds"][0]["retained_upper_ms"], 0.0)

    def test_four_timestamp_ordering_exhaustive_small_domain(self):
        for admitted_ns, input_ack_ns, release_start_ns, release_return_ns in product(range(4), repeat=4):
            events = [
                {"event": "input_admission", "intent_token": "t", "key": "a",
                 "admitted_ns": admitted_ns, "input_ack_ns": input_ack_ns},
                {"event": "input_release_transition", "intent_token": "t", "operation": "up",
                 "key": "a", "release_call_started_ns": release_start_ns,
                 "release_call_returned_ns": release_return_ns,
                 "owner_transition_verified": True},
            ]
            expected = admitted_ns <= input_ack_ns <= release_start_ns <= release_return_ns
            with self.subTest(times=(admitted_ns, input_ack_ns, release_start_ns, release_return_ns)):
                result = candidate.analyze(events)
                self.assertEqual(result["measurement_ready"], expected, result)

    def test_integer_booleans_are_rejected_as_timestamps(self):
        events = [
            {"event": "input_admission", "intent_token": "t", "key": "a",
             "admitted_ns": False, "input_ack_ns": 1},
            {"event": "input_release_transition", "intent_token": "t", "operation": "up",
             "key": "a", "release_call_started_ns": 2,
             "release_call_returned_ns": 3, "owner_transition_verified": True},
        ]
        result = candidate.analyze(events)
        self.assertFalse(result["measurement_ready"], result)
        self.assertEqual(result["invalid_release_count"], 1)

    def test_absent_and_null_intent_tokens_fail_closed(self):
        for token_state in ("absent", "null"):
            with self.subTest(token_state=token_state):
                admission = {"event": "input_admission", "key": "Up",
                             "admitted_ns": 100, "input_ack_ns": 110}
                release = {"event": "input_release_transition", "operation": "up",
                           "key": "Up", "release_call_started_ns": 130,
                           "release_call_returned_ns": 140, "owner_transition_verified": True}
                if token_state == "null":
                    admission["intent_token"] = None
                    release["intent_token"] = None
                result = candidate.analyze([admission, release])
                self.assertFalse(result["measurement_ready"], result)
                self.assertEqual(result["hold_count"], 0)
                self.assertEqual(result["invalid_admission_count"], 1)

    def test_absent_release_intent_token_fails_closed(self):
        events = [
            {"event": "input_admission", "intent_token": "t", "key": "Up",
             "admitted_ns": 100, "input_ack_ns": 110},
            {"event": "input_release_transition", "operation": "up", "key": "Up",
             "release_call_started_ns": 130, "release_call_returned_ns": 140,
             "owner_transition_verified": True},
        ]
        result = candidate.analyze(events)
        self.assertFalse(result["measurement_ready"], result)
        self.assertEqual(result["hold_count"], 0)
        self.assertEqual(result["invalid_release_count"], 1)
        self.assertEqual(result["unmatched_admission_count"], 1)

    def test_missing_or_null_key_admission_invalidates_complete_trace(self):
        for key_state in ("absent", "null"):
            with self.subTest(key_state=key_state):
                events = [
                    {"event": "input_admission", "intent_token": "t", "key": "Up",
                     "admitted_ns": 100, "input_ack_ns": 110},
                    {"event": "input_release_transition", "intent_token": "t", "operation": "up",
                     "key": "Up", "release_call_started_ns": 130,
                     "release_call_returned_ns": 140, "owner_transition_verified": True},
                    {"event": "input_admission", "intent_token": "orphan",
                     "admitted_ns": 200, "input_ack_ns": 210},
                ]
                if key_state == "null":
                    events[-1]["key"] = None
                result = candidate.analyze(events)
                self.assertFalse(result["measurement_ready"], result)
                self.assertEqual(result["hold_count"], 1)
                self.assertEqual(result["invalid_admission_count"], 1)


    def test_malformed_token_and_key_admissions_fail_closed(self):
        malformed = (None, "", 17, True, [], {})
        for field in ("intent_token", "key"):
            for value in malformed:
                with self.subTest(field=field, value=value):
                    admission = {"event": "input_admission", "intent_token": "t", "key": "Up",
                                 "admitted_ns": 100, "input_ack_ns": 110}
                    admission[field] = value
                    release = {"event": "input_release_transition", "intent_token": "t",
                               "operation": "up", "key": "Up", "release_call_started_ns": 130,
                               "release_call_returned_ns": 140, "owner_transition_verified": True}
                    result = candidate.analyze([admission, release])
                    self.assertFalse(result["measurement_ready"], result)
                    self.assertEqual(result["hold_count"], 0, result)
                    self.assertEqual(result["invalid_admission_count"], 1, result)

    def test_malformed_token_and_key_releases_fail_closed(self):
        malformed = (None, "", 17, True, [], {})
        for field in ("intent_token", "key"):
            for value in malformed:
                with self.subTest(field=field, value=value):
                    admission = {"event": "input_admission", "intent_token": "t", "key": "Up",
                                 "admitted_ns": 100, "input_ack_ns": 110}
                    release = {"event": "input_release_transition", "intent_token": "t",
                               "operation": "up", "key": "Up", "release_call_started_ns": 130,
                               "release_call_returned_ns": 140, "owner_transition_verified": True}
                    release[field] = value
                    result = candidate.analyze([admission, release])
                    self.assertFalse(result["measurement_ready"], result)
                    self.assertEqual(result["hold_count"], 0, result)
                    self.assertEqual(result["invalid_release_count"], 1, result)



if __name__ == "__main__":
    unittest.main()
