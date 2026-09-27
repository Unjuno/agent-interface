"""Retained replay for event-driven one-way invalidation."""
import json
import sys
import unittest
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "live_control"))
from event_driven_policy_monitor_v1 import EventDrivenPolicyMonitor, observation_binding
from policy_invalidation_guard_v1 import PolicyInvalidationGuard


class EventDrivenMonitorTest(unittest.TestCase):
    def test_every_dequeued_frame_finds_the_earliest_retained_change(self):
        root = HERE / "results/map01-policy-invalidation-v24-live-01"
        index = json.loads((root / "health-roi-index.json").read_text())
        rows = [row for row in index["rows"] if row["id"] == "cover-4"]
        source = Image.open(root / "frames/decision-04.png").convert("RGB")
        source_sequence = 175
        source_capture_ns = next(row["capture_ns"] for row in rows if row["sequence"] == 176) - 1
        binding = {"input_focus_after": 1, "pointer_binding": {"surface": 1}}
        guard = PolicyInvalidationGuard({
            "op": "policy_invalidation_guard", "guard_id": "event-replay",
            "source_sequence": source_sequence, "box": index["box"],
            "metric": "rgb_change", "rgb_threshold": 32,
            "minimum_changed_pixels": 100, "max_source_age_ms": 30000,
            "on_change": "needs_decision", "on_unknown": "needs_decision",
        }, source, source_sequence, observation_binding(binding), source_capture_ns)

        def load(row):
            frame = source.copy()
            with Image.open(root / row["retained"]) as roi:
                frame.paste(roi.convert("RGB"), (index["box"][0], index["box"][1]))
            return frame

        ticks = iter(range(1, 10000))
        monitor = EventDrivenPolicyMonitor(guard, frame_loader=load, clock=lambda: next(ticks))
        hit = None
        for row in rows:
            hit = monitor.observe({**binding, **row, "image": row["retained"]})
            if hit:
                break
        self.assertIsNotNone(hit)
        self.assertEqual(hit["sequence"], 200)
        self.assertEqual(hit["outcome"]["status"], "INVALIDATED")
        self.assertEqual(hit["outcome"]["changed_pixels"], 921)
        self.assertFalse(hit["outcome"]["grants_input_authority"])

    def test_duplicate_stream_sequence_fails_closed(self):
        source = Image.new("RGB", (10, 10), "black")
        binding = {"input_focus_after": 1, "pointer_binding": {"surface": 1}}
        guard = PolicyInvalidationGuard({
            "op": "policy_invalidation_guard", "guard_id": "duplicate",
            "source_sequence": 1, "box": [2, 2, 8, 8], "metric": "rgb_change",
            "rgb_threshold": 32, "minimum_changed_pixels": 4,
            "max_source_age_ms": 1000, "on_change": "needs_decision",
            "on_unknown": "needs_decision",
        }, source, 1, observation_binding(binding), 100)
        monitor = EventDrivenPolicyMonitor(guard, frame_loader=lambda row: source,
                                           clock=iter(range(10, 100)).__next__)
        self.assertIsNone(monitor.observe({**binding, "sequence": 2, "capture_ns": 200}))
        result = monitor.observe({**binding, "sequence": 2, "capture_ns": 201})
        self.assertEqual(result["outcome"]["status"], "UNKNOWN")
        self.assertTrue(result["outcome"]["requires_new_decision"])


if __name__ == "__main__":
    unittest.main()
