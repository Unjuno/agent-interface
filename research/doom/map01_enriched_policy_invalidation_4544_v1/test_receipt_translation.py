"""Offline tests against receipts emitted by the repository's live monitor."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LIVE_CONTROL = ROOT / "research" / "live_control"
sys.path.insert(0, str(LIVE_CONTROL))
sys.path.insert(0, str(HERE))

from final_action_admission_v1 import decide_final_admission
from observable_signal_guard_v2 import ObservableSignalGuard, ObservableSignalPolicyMonitor
from receipt_translation import translate_monitor_receipt


SESSION = "issue-4544-synthetic-session"
NOW_HOST_NS = 8_577_269_505_000
CALIBRATION_SAMPLE_HOST_NS = NOW_HOST_NS - 10_000_000
PROBE_SAMPLES = [
    {"host_send_ns": CALIBRATION_SAMPLE_HOST_NS - 4_000,
     "runtime_ns": CALIBRATION_SAMPLE_HOST_NS - 4_000 - 739_170_083_874,
     "host_receive_ns": CALIBRATION_SAMPLE_HOST_NS - 3_000},
    {"host_send_ns": CALIBRATION_SAMPLE_HOST_NS - 2_000,
     "runtime_ns": CALIBRATION_SAMPLE_HOST_NS - 2_000 - 739_169_600_000,
     "host_receive_ns": CALIBRATION_SAMPLE_HOST_NS - 1_000},
    {"host_send_ns": CALIBRATION_SAMPLE_HOST_NS - 500,
     "runtime_ns": CALIBRATION_SAMPLE_HOST_NS - 500 - 739_169_181_060,
     "host_receive_ns": CALIBRATION_SAMPLE_HOST_NS},
]
CALIBRATION = {
    "clock_domain": "same_session_host_runtime_monotonic",
    "session_id": SESSION,
    "probe_count": 3,
    "host_clock_domain": "host_monotonic",
    "runtime_clock_domain": "runtime_monotonic",
    "samples": PROBE_SAMPLES,
    "sampled_host_ns": CALIBRATION_SAMPLE_HOST_NS,
    "offset_lower_ns": min(s["runtime_ns"] - s["host_receive_ns"] for s in PROBE_SAMPLES),
    "offset_upper_ns": max(s["runtime_ns"] - s["host_send_ns"] for s in PROBE_SAMPLES),
}
PLANNER_TERMINAL = {
    "turn_id": "synthetic-interrupted-turn",
    "status": "interrupted",
    "answer_eligible": False,
    "terminal_observed_ns": 7_838_099_328_334,
}
DECISION_RUNTIME_NS = 7_838_101_785_959


def monitor_receipt():
    binding = {"focus": 7}
    source = {"status": "observed", "signal_id": "health", "value": 91,
              "sequence": 8, "capture_ns": 8_577_000_000_000,
              "binding": binding}
    spec = {
        "op": "observable_signal_guard", "guard_id": "health-floor",
        "source_sequence": 8, "signal_id": "health", "source_value": 91,
        "hard_minimum": 78, "max_source_age_ms": 30000,
        "on_soft_change": "preserve_existing_policy",
        "on_hard_change": "needs_decision", "on_unknown": "needs_decision",
    }
    guard = ObservableSignalGuard(spec, source, binding)

    class Extractor:
        def read(self, observation):
            return observation["signal"]

    monitor = ObservableSignalPolicyMonitor(guard, Extractor())
    ticks = iter((8_577_269_499_000, 8_577_269_499_200, 8_577_269_500_000))
    with patch("observable_signal_guard_v2.time.perf_counter_ns", side_effect=lambda: next(ticks)):
        event = monitor.observe({
            "sequence": 9,
            "signal": {"status": "observed", "signal_id": "health", "value": 68,
                        "sequence": 9, "capture_ns": 8_577_100_000_000,
                        "binding": binding},
        })
    assert event is not None and event["outcome"]["status"] == "HARD_INVALIDATED"
    return event


class EnrichedReceiptTranslationTests(unittest.TestCase):
    def translate(self, receipt=None, calibration=None, **kwargs):
        return translate_monitor_receipt(
            receipt if receipt is not None else monitor_receipt(),
            calibration if calibration is not None else CALIBRATION,
            SESSION, source_clock_domain=kwargs.pop("source_clock_domain", "host_monotonic"),
            now_host_ns=kwargs.pop("now_host_ns", NOW_HOST_NS))

    def test_accepts_monitor_output_and_preserves_full_envelope(self):
        raw = monitor_receipt()
        translated = self.translate(raw)
        for key, value in raw.items():
            if key == "outcome_evaluated_ns":
                self.assertEqual(translated["outcome_evaluated_host_ns"], value)
            elif key == "outcome":
                self.assertEqual(translated[key], value)
            else:
                self.assertEqual(translated[key], value)
        self.assertEqual(set(raw), {k for k in translated if k not in {
            "outcome_evaluated_host_ns", "outcome_clock_domain", "clock_translation",
            "monitor_received_clock_domain", "signal_extracted_clock_domain",
            "signal_capture_clock_domain"}})
        self.assertEqual(translated["outcome_clock_domain"], "runtime_monotonic")
        self.assertEqual(translated["monitor_received_clock_domain"], "host_monotonic")
        self.assertEqual(translated["signal_capture_clock_domain"], "host_monotonic")
        self.assertIn("signal.capture_ns",
                      translated["clock_translation"]["untouched_host_timestamp_fields"])
        self.assertEqual(translated["clock_translation"]["probe_count"], 3)

    def test_mixed_domain_control_fails_then_translation_rejects_without_input(self):
        raw = monitor_receipt()
        with self.assertRaisesRegex(ValueError, "precedes observed boundary"):
            decide_final_admission(PLANNER_TERMINAL, raw, DECISION_RUNTIME_NS)
        translated = self.translate(raw)
        admission = decide_final_admission(
            PLANNER_TERMINAL, translated, DECISION_RUNTIME_NS)
        self.assertEqual(admission["status"], "REJECTED_POLICY_INVALIDATED")
        self.assertFalse(admission["input_authority_admitted"])
        self.assertFalse(admission["grants_input_authority"])
        self.assertIsNone(admission["executor_admission"])
        self.assertEqual(admission["policy_invalidation"], translated)

    def test_missing_required_field_fails_closed(self):
        raw = monitor_receipt()
        del raw["signal_extracted_ns"]
        with self.assertRaisesRegex(ValueError, "envelope"):
            self.translate(raw)

    def test_additional_envelope_and_outcome_metadata_are_preserved(self):
        raw = monitor_receipt()
        raw["future_monitor_extension"] = {"version": 2, "opaque": [1, 2]}
        raw["outcome"]["future_outcome_extension"] = {"opaque": True}
        translated = self.translate(raw)
        self.assertEqual(translated["future_monitor_extension"], raw["future_monitor_extension"])
        self.assertEqual(translated["outcome"]["future_outcome_extension"],
                         raw["outcome"]["future_outcome_extension"])

    def test_wrong_source_clock_domain_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "source clock domain"):
            self.translate(source_clock_domain="runtime_monotonic")

    def test_outcome_must_be_non_authoritative_and_invalidation_class(self):
        raw = monitor_receipt()
        raw["outcome"]["grants_input_authority"] = True
        with self.assertRaisesRegex(ValueError, "one-way invalidation"):
            self.translate(raw)

    def test_wrong_session_and_probe_count_fail_closed(self):
        for field, value in (("session_id", "other"), ("probe_count", 2),
                             ("samples", PROBE_SAMPLES[:2])):
            calibration = dict(CALIBRATION)
            calibration[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "calibration"):
                self.translate(calibration=calibration)

    def test_overwide_interval_fails_closed(self):
        samples = [dict(row) for row in PROBE_SAMPLES]
        samples[-1]["runtime_ns"] += 1_000_000_001
        calibration = dict(CALIBRATION, samples=samples)
        calibration["offset_upper_ns"] = max(
            row["runtime_ns"] - row["host_send_ns"] for row in samples)
        with self.assertRaisesRegex(ValueError, "uncertainty exceeds"):
            self.translate(calibration=calibration)

    def test_declared_bounds_must_match_all_retained_probes(self):
        calibration = dict(CALIBRATION)
        calibration["offset_lower_ns"] -= 1
        with self.assertRaisesRegex(ValueError, "match all three"):
            self.translate(calibration=calibration)

    def test_stale_or_future_calibration_fails_closed(self):
        for sampled in (NOW_HOST_NS - 5_000_000_001, NOW_HOST_NS + 1):
            shift = sampled - CALIBRATION["sampled_host_ns"]
            samples = [{key: value + shift for key, value in row.items()}
                       for row in PROBE_SAMPLES]
            calibration = dict(CALIBRATION, sampled_host_ns=sampled, samples=samples)
            with self.subTest(sampled=sampled), self.assertRaisesRegex(ValueError, "future-dated|older"):
                self.translate(calibration=calibration)

    def test_reordered_monitor_timestamps_fail_closed(self):
        raw = monitor_receipt()
        raw["signal_extracted_ns"] = raw["monitor_received_ns"] - 1
        with self.assertRaisesRegex(ValueError, "stage timestamps"):
            self.translate(raw)

    def test_nonfinite_stage_duration_fails_closed(self):
        raw = monitor_receipt()
        raw["outcome_evaluation_ms"] = float("nan")
        with self.assertRaisesRegex(ValueError, "durations"):
            self.translate(raw)

    def test_input_is_not_mutated(self):
        raw = monitor_receipt()
        before = deepcopy(raw)
        self.translate(raw)
        self.assertEqual(raw, before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
