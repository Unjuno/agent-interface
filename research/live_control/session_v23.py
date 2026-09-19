"""Candidate X11 backend for agent-authored local visual program barriers."""
import json
import time

from PIL import Image

from executor_v3 import DecisionRequired
from local_visual_barrier_program_v1 import prepare, run
from session_v22 import Backend as Previous, suite


VISUAL_BARRIER_SCHEMA = {
    "op": "local_visual_barrier",
    "placement": "immediately after one admitted mutation and before a later admitted mutation",
    "required": {
        "barrier_id": "unique nonempty string up to 64 characters",
        "source_sequence": "latest observation sequence at whole-program admission",
        "box": "[left,top,right,bottom] integers; 16..65536 pixels",
        "metric": "persistent_rgb_change",
        "rgb_threshold": "integer 1..254",
        "minimum_changed_pixels": "positive integer within box area",
        "required_samples": "integer 2..5",
        "sample_interval_ms": "integer 20..500",
        "timeout_ms": "integer 100..3000; combined program barrier timeout at most 3000",
        "on_unmet": "needs_decision",
    },
    "authority": "condition for already admitted later steps only; no semantic, task-success or new-input authority",
}


class Backend(Previous):
    def __init__(self, session, out, emit):
        super().__init__(session, out, emit)
        self.visual_barriers = {}

    def image(self):
        frame = self.decoder.frame
        if frame is None or frame.mode != "RGB":
            raise ValueError("RGB source observation required")
        return Image.frombytes(frame.mode, (frame.width, frame.height), frame.pixels)

    def frame_identity(self):
        return json.dumps(self.observed_pointer, sort_keys=True)

    def validate(self, steps):
        rewritten, barriers = prepare(
            steps, self.image(), self.sequence, self.frame_identity())
        super().validate(rewritten)
        self.visual_barriers = barriers

    def execute(self, step, cancel, identifier, index):
        if step["op"] != "local_visual_barrier":
            return super().execute(step, cancel, identifier, index)
        barrier = self.visual_barriers.pop(step["barrier_id"], None)
        if barrier is None:
            raise DecisionRequired("local visual barrier identity unavailable")
        captures = 0

        def capture():
            nonlocal captures
            if captures:
                self.snapshot(identifier, index)
            captures += 1
            return self.image(), self.frame_identity(), time.perf_counter_ns()

        return run(step, barrier, capture, cancel, lambda outcome: self.emit({
            "event": "local_visual_barrier", "id": identifier, "step": index,
            "sequence": self.sequence, **outcome,
        }))
