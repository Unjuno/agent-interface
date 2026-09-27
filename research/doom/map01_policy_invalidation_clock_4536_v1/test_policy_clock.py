from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
LIVE_CONTROL = HERE.parents[1] / "live_control"
sys.path.insert(0, str(LIVE_CONTROL))
sys.path.insert(0, str(HERE))

from final_action_admission_v1 import decide_final_admission
from policy_clock import translate_policy_invalidation


SESSION = "fixture-session-4536"
CALIBRATION = {
    "clock_domain": "same_session_host_runtime_monotonic",
    "session_id": SESSION,
    "offset_lower_ns": -739170084874,
    "offset_upper_ns": -739169181060,
}
PLANNER_TERMINAL = {
    "turn_id": "interrupted-turn-8",
    "status": "interrupted",
    "answer_eligible": False,
    "terminal_observed_ns": 7838099328334,
}
DECISION_RUNTIME_NS = 7838101785959
INVALIDATION_HOST_NS = 8577269500000


def invalidation(host_ns=INVALIDATION_HOST_NS):
    return {
        "outcome_evaluated_ns": host_ns,
        "outcome": {
            "status": "HARD_INVALIDATED",
            "reason": "below_hard_minimum",
            "requires_new_decision": True,
            "grants_input_authority": False,
        },
    }


class PolicyClockTests(unittest.TestCase):
    def test_untranslated_mixed_domain_control_raises(self):
        with self.assertRaisesRegex(ValueError, "precedes observed boundary"):
            decide_final_admission(
                PLANNER_TERMINAL, invalidation(), DECISION_RUNTIME_NS)

    def test_converted_invalidation_rejects_without_input_authority(self):
        translated = translate_policy_invalidation(
            invalidation(), CALIBRATION, SESSION)
        self.assertEqual(translated["outcome_evaluated_ns"], 7838100318940)
        self.assertEqual(translated["outcome_evaluated_host_ns"], INVALIDATION_HOST_NS)
        self.assertEqual(translated["outcome_clock_domain"], "runtime_monotonic")
        self.assertEqual(translated["clock_translation"]["mapping_bound"],
                         "latest_possible_runtime_time")

        receipt = decide_final_admission(
            PLANNER_TERMINAL, translated, DECISION_RUNTIME_NS)
        self.assertEqual(receipt["status"], "REJECTED_POLICY_INVALIDATED")
        self.assertEqual(receipt["reason"], "below_hard_minimum")
        self.assertFalse(receipt["input_authority_admitted"])
        self.assertFalse(receipt["grants_input_authority"])
        self.assertIsNone(receipt["executor_admission"])
        self.assertEqual(receipt["policy_invalidation"], translated)

    def test_latest_possible_boundary_must_precede_decision(self):
        translated = translate_policy_invalidation(
            invalidation(), CALIBRATION, SESSION)
        with self.assertRaisesRegex(ValueError, "precedes observed boundary"):
            decide_final_admission(
                PLANNER_TERMINAL, translated,
                translated["outcome_evaluated_ns"] - 1)

    def test_wrong_session_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "same-session"):
            translate_policy_invalidation(
                invalidation(), CALIBRATION, "different-session")

    def test_overwide_calibration_fails_closed(self):
        calibration = dict(CALIBRATION)
        calibration["offset_upper_ns"] += 1_000_000_001
        with self.assertRaisesRegex(ValueError, "uncertainty exceeds"):
            translate_policy_invalidation(invalidation(), calibration, SESSION)

    def test_malformed_calibration_fails_closed(self):
        for field in ("clock_domain", "session_id"):
            calibration = dict(CALIBRATION)
            calibration[field] = "unknown"
            with self.subTest(field=field), self.assertRaises(ValueError):
                translate_policy_invalidation(invalidation(), calibration, SESSION)

    def test_malformed_timestamp_fails_closed(self):
        for timestamp in (True, -1, "8577269500000"):
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                translate_policy_invalidation(invalidation(timestamp), CALIBRATION, SESSION)


if __name__ == "__main__":
    unittest.main(verbosity=2)
