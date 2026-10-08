"""Regression for observations queued as the planner future completes."""
import queue
import unittest
from pathlib import Path

from map01_overlap_controller_v39 import (
    DoomCoverSignalPairMonitor, drain_pending_observation_events)


class Monitor:
    event_types = {"observation", "typed_observation"}

    def __init__(self, invalidate_on=None):
        self.invalidate_on = invalidate_on
        self.seen = []

    def observe(self, row):
        self.seen.append(row["sequence"])
        if row["sequence"] == self.invalidate_on:
            return {"event": "policy_invalidation",
                    "reason": "health:below_hard_minimum",
                    "requires_new_decision": True}
        return None


class SignalGuard:
    def __init__(self, signal_id, source_value, source_sequence,
                 source_capture_ns, hard_minimum):
        self.spec = {"signal_id": signal_id, "source_value": source_value,
                     "source_sequence": source_sequence}
        self.source_capture_ns = source_capture_ns
        self.hard_minimum = hard_minimum

    def evaluate(self, signal):
        invalid = signal["value"] < self.hard_minimum
        changed = signal["value"] != self.spec["source_value"]
        status = ("HARD_INVALIDATED" if invalid else
                  "SOFT_CHANGED" if changed else "UNCHANGED")
        reason = ("below_hard_minimum" if invalid else
                  "within_validity_envelope" if changed else "signal_unchanged")
        return {"status": status,
                "reason": reason,
                "requires_new_decision": invalid}


def typed_signal(signal_id, value, sequence, capture_ns, binding):
    return {"status": "observed", "signal_id": signal_id, "value": value,
            "sequence": sequence, "capture_ns": capture_ns,
            "binding": dict(binding)}


class PendingObservationDrainTests(unittest.TestCase):
    def test_queued_hard_crossing_precedes_completed_answer(self):
        incoming = queue.Queue()
        incoming.put({"event": "typed_observation", "sequence": 12})
        incoming.put({"event": "terminal", "id": "cover-1",
                      "status": "completed",
                      "release": {"verified": True, "keys_down": [],
                                  "buttons_down": []}})
        monitor = Monitor(invalidate_on=12)

        result = drain_pending_observation_events(incoming, monitor, "cover-1")

        self.assertEqual(monitor.seen, [12])
        self.assertEqual(result["invalidation"]["reason"],
                         "health:below_hard_minimum")
        self.assertEqual(result["terminal"]["status"], "completed")
        self.assertTrue(incoming.empty())

    def test_soft_observation_and_terminal_preserve_completed_answer_path(self):
        incoming = queue.Queue()
        incoming.put({"event": "observation", "sequence": 20})
        incoming.put({"event": "terminal", "id": "cover-2",
                      "status": "completed"})
        monitor = Monitor()

        result = drain_pending_observation_events(incoming, monitor, "cover-2")

        self.assertEqual(result["latest"]["sequence"], 20)
        self.assertIsNone(result["invalidation"])
        self.assertEqual(result["terminal"]["id"], "cover-2")


    def test_completed_future_drain_is_wired_before_answer_read(self):
        source = Path(__file__).with_name("map01_overlap_controller_v39.py").read_text(
            encoding="utf-8")
        loop = source.index("while not future.done():")
        drain = source.index("drain_pending_observation_events(", loop)
        result = source.index("planner_result=future.result()", drain)
        discard = source.index("if invalidation is not None:", result)
        eligible = source.index("if not planner_result.answer_eligible:", discard)
        self.assertLess(loop, drain)
        self.assertLess(drain, result)
        self.assertLess(result, discard)
        self.assertLess(discard, eligible)

    def test_empty_backlog_is_nonblocking_and_returns_no_boundary(self):
        incoming = queue.Queue()
        monitor = Monitor()

        result = drain_pending_observation_events(incoming, monitor, "cover-3")

        self.assertEqual(result, {"latest": None, "terminal": None,
                                  "invalidation": None})
        self.assertEqual(monitor.seen, [])

    def test_snapshot_drain_leaves_events_arriving_after_entry_queued(self):
        incoming = queue.Queue()
        incoming.put({"event": "observation", "sequence": 30})

        class EnqueueDuringObserve(Monitor):
            def observe(self, row):
                self.seen.append(row["sequence"])
                incoming.put({"event": "observation", "sequence": 31})
                return None

        monitor = EnqueueDuringObserve()
        result = drain_pending_observation_events(incoming, monitor, "cover-4")

        self.assertEqual(monitor.seen, [30])
        self.assertEqual(result["latest"]["sequence"], 30)
        self.assertEqual(incoming.qsize(), 1)
        self.assertEqual(incoming.get_nowait()["sequence"], 31)

    def test_production_paired_monitor_invalidates_queued_typed_health_crossing(self):
        binding = {"focus": 7, "surface": 9,
                   "geometry": [0, 0, 640, 480]}
        monitor = DoomCoverSignalPairMonitor(
            {"health": SignalGuard("health", 100, 10, 1_000_000_000, 80),
             "ammo": SignalGuard("ammo", 4, 10, 1_000_000_000, 1)},
            health_reader=None, ammo_reader=None)
        row = {
            "event": "typed_observation", "sequence": 11,
            "capture_ns": 1_100_000_000, "pointer_binding": binding,
            "frame_rgb_sha256": "a" * 64,
            "signals": {
                "health": typed_signal("health", 75, 11, 1_100_000_000,
                                        binding),
                "ammo": typed_signal("ammo", 4, 11, 1_100_000_000,
                                      binding),
            },
        }
        incoming = queue.Queue()
        incoming.put(row)

        result = drain_pending_observation_events(incoming, monitor, "cover-5")

        self.assertEqual(result["invalidation"]["event"],
                         "paired_signal_invalidation")
        self.assertEqual(result["invalidation"]["reason"],
                         "health:below_hard_minimum")
        self.assertTrue(incoming.empty())

    def test_production_monitor_preserves_cover_on_soft_typed_health_change(self):
        binding = {"focus": 7, "surface": 9,
                   "geometry": [0, 0, 640, 480]}
        monitor = DoomCoverSignalPairMonitor(
            {"health": SignalGuard("health", 100, 10, 1_000_000_000, 80),
             "ammo": SignalGuard("ammo", 4, 10, 1_000_000_000, 1)},
            health_reader=None, ammo_reader=None)
        incoming = queue.Queue()
        incoming.put({
            "event": "typed_observation", "sequence": 11,
            "capture_ns": 1_100_000_000, "pointer_binding": binding,
            "frame_rgb_sha256": "b" * 64,
            "signals": {
                "health": typed_signal("health", 95, 11, 1_100_000_000,
                                        binding),
                "ammo": typed_signal("ammo", 4, 11, 1_100_000_000,
                                      binding),
            },
        })

        result = drain_pending_observation_events(incoming, monitor, "cover-6")

        self.assertIsNone(result["invalidation"])
        self.assertIsNone(result["latest"])
        self.assertEqual(monitor.soft_event_count, 1)
        self.assertEqual(monitor.latest_soft_event["sequence"], 11)
        self.assertEqual(monitor.latest_soft_event["signal"]["value"], 95)


if __name__ == "__main__":
    unittest.main(verbosity=2)

