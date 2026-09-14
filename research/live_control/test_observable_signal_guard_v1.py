import copy
import unittest

from research.live_control.observable_signal_guard_v1 import (
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
    def read(self, observation):
        return observation["signal"]


class ObservableSignalGuardTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
