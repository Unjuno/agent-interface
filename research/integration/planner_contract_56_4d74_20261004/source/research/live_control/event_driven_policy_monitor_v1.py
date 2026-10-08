"""Evaluate a one-way policy guard on every dequeued observation."""
import json
import time
from pathlib import Path

from PIL import Image


def observation_binding(observation):
    return json.dumps({
        "input_focus_after": observation.get("input_focus_after"),
        "pointer_binding": observation.get("pointer_binding"),
    }, sort_keys=True, separators=(",", ":"))


class EventDrivenPolicyMonitor:
    def __init__(self, guard, frame_loader=None, clock=None):
        self.guard = guard
        self.frame_loader = frame_loader or self._load_frame
        self.clock = clock or time.perf_counter_ns
        self.last_sequence = guard.spec["source_sequence"]

    @staticmethod
    def _load_frame(observation):
        with Image.open(Path(observation["image"])) as opened:
            return opened.convert("RGB")

    def observe(self, observation):
        dequeued_ns = self.clock()
        sequence = observation.get("sequence")
        if type(sequence) is not int or sequence <= self.last_sequence:
            outcome = self._unknown("nonadvancing_stream_sequence")
        else:
            self.last_sequence = sequence
            try:
                frame = self.frame_loader(observation)
            except (KeyError, OSError, ValueError):
                frame = None
            outcome = self.guard.evaluate(
                frame, sequence, observation_binding(observation),
                observation.get("capture_ns"))
        evaluated_ns = self.clock()
        record = {
            "outcome": outcome,
            "sequence": sequence,
            "image": observation.get("image"),
            "capture_ns": observation.get("capture_ns"),
            "dequeued_ns": dequeued_ns,
            "evaluated_ns": evaluated_ns,
            "detected_ns": evaluated_ns,
            "evaluation_ms": (evaluated_ns - dequeued_ns) / 1e6,
        }
        return None if outcome["status"] == "UNCHANGED" else record

    def _unknown(self, reason):
        return {
            "format": "policy-invalidation-outcome-v1",
            "guard_id": self.guard.spec["guard_id"],
            "status": "UNKNOWN", "reason": reason,
            "keep_existing_policy": False, "requires_new_decision": True,
            "changed_pixels": 0,
            "minimum_changed_pixels": self.guard.spec["minimum_changed_pixels"],
            "source_age_ms": None, "grants_input_authority": False,
            "may_only_reduce_existing_authority": True,
            "semantic_change_identified": False, "task_success_verified": False,
        }
