import copy
import unittest
from unittest.mock import patch

from research.live_control.observable_signal_guard_v2 import (
    ObservableSignalGuard, ObservableSignalPolicyMonitor,
)
from research.live_control.final_action_admission_v1 import decide_final_admission
from research.doom.map01_enriched_receipt_audit_4544_v1.receipt_translation_v2 import (
    translate_enriched_receipt,
)


SESSION = "decision-8-synthetic-receipt-test"
HOST_DECISION = 8_577_271_870_833
RUNTIME_DECISION = 7_838_101_785_959
PLANNER_TERMINAL_RUNTIME = 7_838_099_328_334
EVENT_HOST_TIME = 8_577_269_500_000  # explicitly synthetic; original receipt absent
PROBES = [
    {"host_receive_ns": 8_577_270_229_750, "host_send_ns": 8_577_269_454_041,
     "offset_lower_ns": -739_170_042_417, "offset_upper_ns": -739_169_266_708,
     "runtime_ns": 7_838_100_187_333},
    {"host_receive_ns": 8_577_271_073_333, "host_send_ns": 8_577_270_231_333,
     "offset_lower_ns": -739_170_023_060, "offset_upper_ns": -739_169_181_060,
     "runtime_ns": 7_838_101_050_273},
    {"host_receive_ns": 8_577_271_864_750, "host_send_ns": 8_577_271_074_208,
     "offset_lower_ns": -739_170_084_874, "offset_upper_ns": -739_169_294_332,
     "runtime_ns": 7_838_101_779_876},
]
CALIBRATION = {"session_id": SESSION, "samples": PROBES}
BOUNDING = {"surface": 77, "geometry": [1, 2, 640, 480]}


def monitor_event():
    source = {"format": "observable-signal-v1", "status": "observed",
              "signal_id": "health", "value": 97, "sequence": 32,
              "capture_ns": EVENT_HOST_TIME - 1_000_000,
              "binding": BOUNDING}
    spec = {"op": "observable_signal_guard", "guard_id": "map01-0",
            "source_sequence": 32, "signal_id": "health", "source_value": 97,
            "hard_minimum": 97, "max_source_age_ms": 30000,
            "on_soft_change": "preserve_existing_policy",
            "on_hard_change": "needs_decision", "on_unknown": "needs_decision"}
    guard = ObservableSignalGuard(spec, source, BOUNDING)

    class Extractor:
        def read(self, observation):
            return observation["signal"]

    monitor = ObservableSignalPolicyMonitor(guard, Extractor())
    changed = {"format": "observable-signal-v1", "status": "observed",
               "signal_id": "health", "value": 91, "sequence": 33,
               "capture_ns": EVENT_HOST_TIME - 500_000,
               "binding": BOUNDING, "fixture_tag": "monitor-source-derived"}
    ticks = iter((EVENT_HOST_TIME, EVENT_HOST_TIME + 1_000,
                  EVENT_HOST_TIME + 2_000))
    with patch("research.live_control.observable_signal_guard_v2.time.perf_counter_ns",
               side_effect=lambda: next(ticks)):
        return monitor.observe({"sequence": 33, "signal": changed})


class EnrichedReceiptTranslationTests(unittest.TestCase):
    def test_actual_monitor_envelope_translates_and_final_gate_rejects(self):
        event = monitor_event()
        self.assertEqual(event["outcome"]["status"], "HARD_INVALIDATED")
        self.assertEqual(set(("sequence", "signal", "outcome", "monitor_received_ns",
                             "signal_extracted_ns", "outcome_evaluated_ns",
                             "signal_extraction_ms", "outcome_evaluation_ms")) - set(event), set())
        translated = translate_enriched_receipt(event, CALIBRATION, SESSION, HOST_DECISION)
        self.assertEqual(translated["outcome_evaluated_host_ns"], EVENT_HOST_TIME + 2_000)
        self.assertEqual(translated["outcome_clock_domain"], "runtime_monotonic")
        self.assertEqual(translated["receipt_origin"],
                         "synthetic_monitor_event_missing_from_predecessor")
        for key, value in event.items():
            if key != "outcome_evaluated_ns":
                self.assertEqual(translated[key], value)
        result = decide_final_admission(
            {"turn_id": "synthetic-turn", "status": "completed",
             "answer_eligible": True, "terminal_observed_ns": PLANNER_TERMINAL_RUNTIME},
            translated, RUNTIME_DECISION)
        self.assertEqual(result["status"], "REJECTED_POLICY_INVALIDATED")
        self.assertFalse(result["input_authority_admitted"])
        self.assertIsNone(result["executor_admission"])

    def test_semantic_roundtrip_preserves_extra_metadata(self):
        event = monitor_event()
        event["vendor_extension"] = {"nested": [1, "keep", False]}
        translated = translate_enriched_receipt(event, CALIBRATION, SESSION, HOST_DECISION)
        self.assertEqual(translated["vendor_extension"], event["vendor_extension"])
        self.assertEqual(translated["signal"]["fixture_tag"], "monitor-source-derived")
        self.assertEqual(translated["outcome"], event["outcome"])

    def test_unconverted_host_receipt_does_not_mix_clock_domains(self):
        event = monitor_event()
        with self.assertRaises(ValueError):
            decide_final_admission(
                {"turn_id": "synthetic-turn", "status": "completed",
                 "answer_eligible": True, "terminal_observed_ns": PLANNER_TERMINAL_RUNTIME},
                event, RUNTIME_DECISION)

    def test_wrong_session_fails_closed(self):
        with self.assertRaises(ValueError):
            translate_enriched_receipt(monitor_event(), CALIBRATION, "other-session",
                                       HOST_DECISION)

    def test_missing_or_additional_probe_fails_closed(self):
        for probes in (PROBES[:2], PROBES + [PROBES[-1]]):
            with self.subTest(count=len(probes)), self.assertRaises(ValueError):
                translate_enriched_receipt(
                    monitor_event(),
                    {"session_id": SESSION, "samples": probes}, SESSION,
                    HOST_DECISION)

    def test_overwide_clock_uncertainty_fails_closed(self):
        record = copy.deepcopy(CALIBRATION)
        record["samples"][1]["offset_upper_ns"] = 300_000_000
        with self.assertRaises(ValueError):
            translate_enriched_receipt(monitor_event(), record, SESSION, HOST_DECISION)

    def test_stale_probe_and_future_receipt_fail_closed(self):
        stale = copy.deepcopy(CALIBRATION)
        stale["samples"][2]["host_receive_ns"] -= 6_000_000_000
        with self.assertRaises(ValueError):
            translate_enriched_receipt(monitor_event(), stale, SESSION, HOST_DECISION)
        future = monitor_event()
        future["outcome_evaluated_ns"] = HOST_DECISION + 1
        with self.assertRaises(ValueError):
            translate_enriched_receipt(future, CALIBRATION, SESSION, HOST_DECISION)

    def test_malformed_or_authority_granting_receipt_fails_closed(self):
        malformed = monitor_event()
        del malformed["signal_extracted_ns"]
        with self.assertRaises(ValueError):
            translate_enriched_receipt(malformed, CALIBRATION, SESSION, HOST_DECISION)
        forged = monitor_event()
        forged["outcome"]["grants_input_authority"] = True
        with self.assertRaises(ValueError):
            translate_enriched_receipt(forged, CALIBRATION, SESSION, HOST_DECISION)


if __name__ == "__main__":
    unittest.main()
