"""Counterfactual sensitivity of the current V39 guard to a retained HUD trace.

Posthoc deterministic replay only. The source values are manually transcribed
from retained Astra video and were not consumed by that controller run.
"""
import hashlib
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOOM = HERE.parent
sys.path[:0] = [str(DOOM), str(DOOM.parent / "live_control")]
import map01_overlap_controller_v39 as controller

CONTROLLER_SHA256 = "f76c618f5eedbe2c301eecb67c36c9064ec0de035009d0be6f8610bb1d808dc8"
ASTRA_RESULT_SHA256 = "9b7ab8826bf56073ec9425f6ff0d80acd70990032688ea1505c125df4e3035b7"


class Reader:
    def __init__(self, rows):
        self.rows = rows

    def read(self, observation):
        return self.rows[observation["sequence"]]


def signal(value, sequence, capture_ns, binding):
    return {"format": "observable-signal-v1", "status": "observed",
            "signal_id": "health", "value": value, "sequence": sequence,
            "capture_ns": capture_ns, "binding": binding}


class TransientHealthGuardSensitivityTests(unittest.TestCase):
    def test_retained_seven_point_excursion_against_current_main_guard(self):
        controller_path = DOOM / "map01_overlap_controller_v39.py"
        astra_result_path = DOOM / "astra_continuous_hud_a01" / "result.json"
        self.assertEqual(hashlib.sha256(controller_path.read_bytes()).hexdigest(),
                         CONTROLLER_SHA256)
        self.assertEqual(hashlib.sha256(astra_result_path.read_bytes()).hexdigest(),
                         ASTRA_RESULT_SHA256)
        source = json.loads(astra_result_path.read_text(encoding="utf-8"))
        observation = source["observation"]
        self.assertEqual(source["status"], "POSTHOC_PASS_SCOPED")
        self.assertTrue(observation["manual_visual_transcription"])
        health_values = (observation["decision_before_health_percent_manual"],
                         observation["selected_health_percent_manual"],
                         observation["decision_after_health_percent_manual"])
        self.assertEqual(health_values, (84, 77, 84))

        binding = {"focus": 1, "surface": 1, "geometry": [0, 0, 640, 480]}
        source_observation = {"event": "observation", "sequence": 210,
                              "capture_ns": 1_000_000_000,
                              "pointer_binding": binding}
        rows = {210: signal(84, 210, 1_000_000_000, binding),
                211: signal(77, 211, 1_200_000_000, binding),
                212: signal(84, 212, 1_400_000_000, binding)}
        cases = []

        def evaluate(*, critical_minimum, maximum_loss):
            monitor, admission = controller.build_cover_monitor(
                Reader(rows), source_observation,
                {"signal_id": "health",
                 "critical_health_minimum": critical_minimum,
                 "maximum_health_loss": maximum_loss,
                 "max_source_age_ms": 30000}, 5)
            middle_event = monitor.observe({"event": "observation", "sequence": 211,
                "capture_ns": 1_200_000_000, "pointer_binding": binding})
            recovered_event = monitor.observe({"event": "observation", "sequence": 212,
                "capture_ns": 1_400_000_000, "pointer_binding": binding})
            return {"critical_health_minimum": critical_minimum,
                    "maximum_health_loss": maximum_loss,
                    "hard_minimum": monitor.guard.spec["hard_minimum"],
                    "admission": admission["status"],
                    "transient_outcome": (None if middle_event is None else
                        middle_event["outcome"]["status"]),
                    "transient_reason": (None if middle_event is None else
                        middle_event["outcome"]["reason"]),
                    "soft_event_count": monitor.soft_event_count,
                    "recovery_outcome": (None if recovered_event is None else
                        recovered_event["outcome"]["status"]),
                    "input_authority_granted": False}

        for loss in range(21):
            cases.append(evaluate(critical_minimum=35, maximum_loss=loss))
        for critical in (35, 77, 78, 84):
            cases.append(evaluate(critical_minimum=critical, maximum_loss=12))

        for case in cases[:21]:
            expected = ("HARD_INVALIDATED" if case["hard_minimum"] > 77
                        else None)
            self.assertEqual(case["transient_outcome"], expected,
                             msg=f"maximum_health_loss={case['maximum_health_loss']}")
        self.assertEqual(cases[6]["hard_minimum"], 78)
        self.assertEqual(cases[6]["transient_outcome"], "HARD_INVALIDATED")
        self.assertEqual(cases[7]["hard_minimum"], 77)
        self.assertIsNone(cases[7]["transient_outcome"])
        self.assertEqual(cases[7]["soft_event_count"], 1)
        self.assertEqual(cases[12]["hard_minimum"], 72)
        self.assertIsNone(cases[12]["transient_outcome"])
        self.assertEqual(cases[22]["hard_minimum"], 77)
        self.assertIsNone(cases[22]["transient_outcome"])
        self.assertEqual(cases[23]["hard_minimum"], 78)
        self.assertEqual(cases[23]["transient_outcome"], "HARD_INVALIDATED")

        raw = {"schema": "v39-retained-hud-health-guard-sensitivity-a01-v1",
               "status": "COUNTERFACTUAL_SENSITIVITY_PASS",
               "controller_sha256": CONTROLLER_SHA256,
               "astra_result_sha256": ASTRA_RESULT_SHA256,
               "source_health_manual": 84, "transient_health_manual": 77,
               "recovery_health_manual": 84,
               "critical_minimum_sweep_fixed_at": 35,
               "maximum_loss_sweep": list(range(21)),
               "cases": cases,
               "decision_boundary": {
                   "invalidate_when": "max(critical_health_minimum, source_health - maximum_health_loss) > transient_health",
                   "at_source_84_transient_77":
                       "maximum_health_loss <= 6 or critical_health_minimum >= 78",
                   "equality_at_77": "SOFT_CHANGED; existing cover remains admitted"},
               "limits": [
                   "Retained video HUD values are manually transcribed posthoc.",
                   "The original controller did not consume the intermediate frame.",
                   "No model-authored validity policy for this sample is retained.",
                   "This is deterministic threshold sensitivity, not a live response or outcome.",
                   "No game, model, GUI, OS input, or formal/live allocation was used."],
               "cases_sha256": hashlib.sha256(json.dumps(
                   cases, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
        output = HERE / ("raw-health-sensitivity-optimized.json" if sys.flags.optimize
                         else "raw-health-sensitivity-normal.json")
        output.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n",
                          encoding="utf-8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
