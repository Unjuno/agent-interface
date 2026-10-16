import copy
import unittest

from research.live_control.observable_signal_guard_v2 import (
    ObservableSignalGuard, ObservableSignalPolicyMonitor)


def signal(value=93, sequence=37, capture_ns=1_000_000_000, binding=None):
    return {"format": "observable-signal-v1", "status": "observed", "signal_id": "health",
            "value": value, "sequence": sequence, "capture_ns": capture_ns,
            "binding": binding or {"surface": 1, "geometry": [1, 2, 640, 480]}}


def spec():
    return {"op": "observable_signal_guard", "guard_id": "g", "source_sequence": 37,
            "signal_id": "health", "source_value": 93, "hard_minimum": 80,
            "max_source_age_ms": 30000, "on_soft_change": "preserve_existing_policy",
            "on_hard_change": "needs_decision", "on_unknown": "needs_decision"}


class Extractor:
    def __init__(self):
        self.calls = 0

    def read(self, observation):
        self.calls += 1
        return observation["signal"]


def typed_observation(health, *, sequence=38, capture_ns=1_100_000_000):
    health = dict(health, sequence=sequence, capture_ns=capture_ns,
                  wad_sha256="b" * 64)
    ammo = {"format": "observable-signal-v1", "status": "observed",
            "signal_id": "ammo", "value": 20, "sequence": sequence,
            "capture_ns": capture_ns, "binding": health["binding"],
            "wad_sha256": "b" * 64}
    return {
        "event": "typed_observation", "schema": "doom-typed-observation-v1",
        "id": "sample-38", "step": 0, "sequence": sequence,
        "capture_ns": capture_ns, "pointer_binding": health["binding"],
        "signals": {"health": health, "ammo": ammo},
        "frame_rgb_sha256": "a" * 64, "frame_size": [640, 480],
        "typed_extraction_started_ns": capture_ns + 1,
        "typed_ready_ns": capture_ns + 2,
        "capture_to_typed_ready_ms": 0.000002,
        "artifact_published": False, "grants_input_authority": False,
    }


class ObservableSignalGuardV2Tests(unittest.TestCase):
    def test_health_only_monitor_uses_typed_signal_before_artifact(self):
        extractor = Extractor()
        monitor = ObservableSignalPolicyMonitor(
            ObservableSignalGuard(spec(), signal(), signal()["binding"]), extractor)
        typed = typed_observation(signal(87))

        self.assertIn("typed_observation", monitor.event_types)
        self.assertIsNone(monitor.observe(typed))
        self.assertEqual(extractor.calls, 0)
        self.assertEqual(monitor.latest_soft_event["signal"]["value"], 87)
        self.assertEqual(monitor.latest_soft_event["outcome"]["status"], "SOFT_CHANGED")
        self.assertFalse(monitor.latest_soft_event["outcome"]["grants_input_authority"])

    def test_health_only_monitor_invalidates_on_typed_hard_signal(self):
        extractor = Extractor()
        monitor = ObservableSignalPolicyMonitor(
            ObservableSignalGuard(spec(), signal(), signal()["binding"]), extractor)

        event = monitor.observe(typed_observation(signal(79)))

        self.assertEqual(event["outcome"]["status"], "HARD_INVALIDATED")
        self.assertFalse(event["outcome"]["grants_input_authority"])
        self.assertEqual(extractor.calls, 0)

    def test_health_only_monitor_fails_closed_on_malformed_typed_epoch(self):
        extractor = Extractor()
        monitor = ObservableSignalPolicyMonitor(
            ObservableSignalGuard(spec(), signal(), signal()["binding"]), extractor)
        typed = typed_observation(signal(87))
        typed["signals"]["health"]["capture_ns"] += 1

        event = monitor.observe(typed)

        self.assertEqual(event["outcome"]["status"], "UNKNOWN")
        self.assertFalse(event["outcome"]["grants_input_authority"])
        self.assertEqual(extractor.calls, 0)

    def test_typed_observation_cannot_claim_input_authority(self):
        monitor = ObservableSignalPolicyMonitor(
            ObservableSignalGuard(spec(), signal(), signal()["binding"]), Extractor())
        typed = typed_observation(signal(87))
        typed["grants_input_authority"] = True

        event = monitor.observe(typed)

        self.assertEqual(event["outcome"]["status"], "UNKNOWN")
        self.assertFalse(event["outcome"]["grants_input_authority"])

    def test_matching_full_artifact_after_typed_event_is_not_a_second_sample(self):
        extractor = Extractor()
        monitor = ObservableSignalPolicyMonitor(
            ObservableSignalGuard(spec(), signal(), signal()["binding"]), extractor)
        typed = typed_observation(signal(87))
        self.assertIsNone(monitor.observe(typed))

        duplicate = {"event": "observation", "sequence": 38,
                     "frame_rgb_sha256": typed["frame_rgb_sha256"],
                     "signal": typed["signals"]["health"]}
        self.assertIsNone(monitor.observe(duplicate))
        self.assertEqual(extractor.calls, 1)
        self.assertEqual(monitor.soft_event_count, 1)

    def test_same_epoch_artifact_with_different_frame_hash_fails_closed(self):
        extractor = Extractor()
        monitor = ObservableSignalPolicyMonitor(
            ObservableSignalGuard(spec(), signal(), signal()["binding"]), extractor)
        typed = typed_observation(signal(87))
        self.assertIsNone(monitor.observe(typed))
        duplicate = {"event": "observation", "sequence": 38,
                     "frame_rgb_sha256": "f" * 64,
                     "signal": typed["signals"]["health"]}

        event = monitor.observe(duplicate)

        self.assertEqual(event["outcome"]["status"], "UNKNOWN")
        self.assertFalse(event["outcome"]["grants_input_authority"])

    def test_soft_hard_and_unchanged_authority(self):
        guard = ObservableSignalGuard(spec(), signal(), signal()["binding"])
        unchanged = guard.evaluate(signal(93, 38, 1_100_000_000))
        soft = guard.evaluate(signal(87, 39, 1_200_000_000))
        hard = guard.evaluate(signal(79, 40, 1_300_000_000))
        self.assertEqual([unchanged["status"], soft["status"], hard["status"]],
                         ["UNCHANGED", "SOFT_CHANGED", "HARD_INVALIDATED"])
        self.assertTrue(unchanged["keep_existing_policy"] and soft["keep_existing_policy"])
        self.assertFalse(hard["keep_existing_policy"])
        self.assertTrue(all(not row["grants_input_authority"] for row in (unchanged, soft, hard)))

    def test_unknown_conditions_fail_closed(self):
        guard = ObservableSignalGuard(spec(), signal(), signal()["binding"])
        cases = [
            {"status": "unknown"},
            signal(90, 37, 1_100_000_000),
            signal(90, 38, 999_999_999),
            signal(90, 38, 31_100_000_000),
            signal(90, 38, 1_100_000_000, {"surface": 2}),
        ]
        for case in cases:
            outcome = guard.evaluate(case)
            self.assertEqual(outcome["status"], "UNKNOWN")
            self.assertTrue(outcome["requires_new_decision"])
            self.assertFalse(outcome["keep_existing_policy"])

    def test_strict_spec_and_source_binding(self):
        for mutate in (
            lambda row: row.update(extra=True),
            lambda row: row.update(source_value=True),
            lambda row: row.update(hard_minimum=94),
            lambda row: row.update(on_soft_change="ignore"),
        ):
            candidate = copy.deepcopy(spec())
            mutate(candidate)
            with self.assertRaises(ValueError):
                ObservableSignalGuard(candidate, signal(), signal()["binding"])
        with self.assertRaises(ValueError):
            ObservableSignalGuard(spec(), signal(92), signal()["binding"])
        with self.assertRaises(ValueError):
            ObservableSignalGuard(spec(), signal(), {"surface": 2})

    def test_monitor_coalesces_soft_values_and_surfaces_hard(self):
        guard = ObservableSignalGuard(spec(), signal(), signal()["binding"])
        monitor = ObservableSignalPolicyMonitor(guard, Extractor())
        for row in (signal(87, 38, 1_100_000_000), signal(87, 39, 1_200_000_000),
                    signal(81, 40, 1_300_000_000)):
            self.assertIsNone(monitor.observe({"sequence": row["sequence"], "signal": row}))
        self.assertEqual(monitor.soft_event_count, 2)
        self.assertEqual(monitor.latest_soft_event["signal"]["value"], 81)
        hard = signal(79, 41, 1_400_000_000)
        event = monitor.observe({"sequence": 41, "signal": hard})
        self.assertEqual(event["outcome"]["status"], "HARD_INVALIDATED")
        self.assertLessEqual(event["monitor_received_ns"], event["signal_extracted_ns"])
        self.assertLessEqual(event["signal_extracted_ns"], event["outcome_evaluated_ns"])
        self.assertGreaterEqual(event["signal_extraction_ms"], 0)
        self.assertGreaterEqual(event["outcome_evaluation_ms"], 0)


if __name__ == "__main__":
    unittest.main()
