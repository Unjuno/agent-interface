from pathlib import Path
import importlib.util
import json
import sys
import unittest
from copy import deepcopy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "research" / "live_control"))

from clock_translation_v2 import SCHEMA, translate_invalidation
from final_action_admission_v1 import decide_final_admission

V1_PATH = HERE.parents[2] / "research/doom/map01_policy_invalidation_clock_4536_v1/clock_translation.py"
V1_SPEC = importlib.util.spec_from_file_location("failed_v1_clock_translation", V1_PATH)
V1 = importlib.util.module_from_spec(V1_SPEC)
V1_SPEC.loader.exec_module(V1)


def retained_calibration():
    repo = HERE.parents[2]
    path = (repo / "research/doom/map01_model_loop_finite_v10/results/"
            "map01-model-loop-finite-v10-20260927-02/runtime/"
            "action-freshness-clock-translations.jsonl")
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    prior = next(row for row in rows if row.get("iteration") == 8 and
                 "planner_terminal_runtime_ns" in row)
    calibration = {"schema": SCHEMA, "same_session": True,
                   "host_domain": "host_monotonic_ns",
                   "runtime_domain": "runtime_monotonic_ns",
                   "samples": prior["samples"]}
    return prior, calibration


def production_shaped_receipt(host_ns):
    return {
        "sequence": 245,
        "signal": {"format": "observable-signal-v1", "signal_id": "health",
                   "status": "observed", "value": 68, "sequence": 245,
                   "capture_ns": host_ns - 2_000_000},
        "monitor_received_ns": host_ns - 300_000,
        "signal_extracted_ns": host_ns - 100_000,
        "outcome_evaluated_ns": host_ns,
        "signal_extraction_ms": 0.2,
        "outcome_evaluation_ms": 0.1,
        "timestamp_domain": "host_monotonic_ns",
        "outcome": {
            "format": "observable-signal-guard-outcome-v1",
            "guard_id": "cover-health",
            "signal_id": "health",
            "status": "HARD_INVALIDATED",
            "reason": "below_hard_minimum",
            "source_value": 91,
            "current_value": 68,
            "hard_minimum": 78,
            "source_age_ms": 100.0,
            "keep_existing_policy": False,
            "requires_new_decision": True,
            "grants_input_authority": False,
            "may_only_preserve_or_reduce_existing_authority": True,
            "semantic_change_identified": True,
            "task_success_verified": False,
        },
    }


class EnrichedPolicyInvalidationClockTests(unittest.TestCase):
    def test_real_retained_probes_and_production_shape_reject_without_input(self):
        prior, calibration = retained_calibration()
        host_event = 8_577_271_000_000  # synthetic; predecessor receipt was lost
        receipt = production_shaped_receipt(host_event)
        with self.assertRaisesRegex(ValueError, "exact host-domain"):
            V1.translate_invalidation(receipt, {
                "schema": V1.SCHEMA, "same_session": True,
                "host_domain": "host_monotonic_ns",
                "runtime_domain": "runtime_monotonic_ns",
                "samples": calibration["samples"]})

        record, runtime_receipt = translate_invalidation(receipt, calibration)
        self.assertEqual(record["source_receipt"], receipt)
        self.assertEqual(runtime_receipt["sequence"], receipt["sequence"])
        self.assertEqual(runtime_receipt["signal"], receipt["signal"])
        self.assertEqual(runtime_receipt["outcome"], receipt["outcome"])
        self.assertEqual(runtime_receipt["timestamp_domain"], "runtime_monotonic_ns")
        expected_runtime_receipt = deepcopy(receipt)
        expected_runtime_receipt["timestamp_domain"] = "runtime_monotonic_ns"
        expected_runtime_receipt["outcome_evaluated_ns"] = record["runtime_timestamp_ns"]
        self.assertEqual(runtime_receipt, expected_runtime_receipt)
        self.assertLessEqual(runtime_receipt["outcome_evaluated_ns"],
                             prior["controller_decided_runtime_ns"])

        terminal = {"turn_id": "interrupted-stale", "status": "interrupted",
                    "answer_eligible": False,
                    "terminal_observed_ns": prior["planner_terminal_runtime_ns"]}
        rejected = decide_final_admission(
            terminal, runtime_receipt, prior["controller_decided_runtime_ns"])
        self.assertEqual(rejected["status"], "REJECTED_POLICY_INVALIDATED")
        self.assertFalse(rejected["input_authority_admitted"])
        self.assertIsNone(rejected["executor_admission"])

    def test_zero_model_preflight_has_actual_empty_owner_releases(self):
        path = (HERE / "preflight/container-startup-zero-decision-20260927-01/"
                "runtime/owner-events.json")
        releases = json.loads(path.read_text())
        self.assertEqual(len(releases), 3)
        self.assertTrue(all(row.get("event") == "owner_release" and
                            row.get("verified") is True and
                            row.get("keys_down") == [] and
                            row.get("buttons_down") == [] for row in releases))
        preflight = json.loads((path.parent / "submit-clock-zero-decision.json").read_text())
        self.assertEqual(preflight["model_turns"], 0)

    def test_wrong_domain_and_missing_calibration_fail_closed(self):
        _, calibration = retained_calibration()
        receipt = production_shaped_receipt(8_577_271_000_000)
        receipt["timestamp_domain"] = "runtime_monotonic_ns"
        with self.assertRaisesRegex(ValueError, "not host monotonic"):
            translate_invalidation(receipt, calibration)
        receipt["timestamp_domain"] = "host_monotonic_ns"
        calibration["same_session"] = False
        with self.assertRaisesRegex(ValueError, "same-session"):
            translate_invalidation(receipt, calibration)

    def test_overwide_and_incomplete_probes_fail_closed(self):
        _, calibration = retained_calibration()
        receipt = production_shaped_receipt(8_577_271_000_000)
        wide = json.loads(json.dumps(calibration))
        wide["samples"][0]["host_send_ns"] -= 2_000_000_000
        with self.assertRaisesRegex(ValueError, "uncertainty"):
            translate_invalidation(receipt, wide)
        short = json.loads(json.dumps(calibration))
        short["samples"] = short["samples"][:2]
        with self.assertRaisesRegex(ValueError, "three clock-offset"):
            translate_invalidation(receipt, short)


if __name__ == "__main__":
    unittest.main()
