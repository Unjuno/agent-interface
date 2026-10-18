"""Candidate backend for minting and revalidating scoped target handles."""
import time

from scoped_target_handle_v2 import TargetHandleStore
from session_v26 import Backend as Previous, suite


MINT = "target_handle_mint"
TARGET_CLICK = "pointer_click_target"
REFUSAL = "target_handle_refusal"


class Backend(Previous):
    def __init__(self, session, out, emit):
        super().__init__(session, out, emit)
        self.handles = TargetHandleStore("x11:" + session.name)
        self.last_capture_ns = None

    def snapshot(self, identifier, index):
        observations = []
        emit = self.emit

        def collect(record):
            if record.get("event") == "observation":
                observations.append(record)
            emit(record)

        self.emit = collect
        try:
            result = super().snapshot(identifier, index)
        finally:
            self.emit = emit
        if not observations:
            raise RuntimeError("snapshot did not emit an observation")
        self.last_capture_ns = observations[-1]["capture_ns"]
        return result

    def observation(self):
        if self.observed_pointer is None or self.last_capture_ns is None:
            raise ValueError("stable current observation required")
        return {"sequence": self.sequence, "capture_ns": self.last_capture_ns,
                "pointer_binding": self.observed_pointer}

    def prepare(self, steps, identifier):
        prepared, records = super().prepare(steps, identifier)
        resolved = []
        now_ns = time.perf_counter_ns()
        for index, step in enumerate(prepared):
            if not isinstance(step, dict) or step.get("op") != TARGET_CLICK:
                resolved.append(step)
                continue
            if set(step) != {"op", "target_handle", "offset", "button", "duration_ms"}:
                raise ValueError("invalid target-handle click fields")
            outcome = self.handles.resolve_point(
                step["target_handle"], step["offset"], self.observation(), self.image(),
                now_ns, session_scope="x11:" + self.session.name)
            record = {"event": "target_handle_revalidated", "step": index, **outcome}
            records.append(record)
            if outcome["eligible"]:
                resolved.append({"op": "pointer_click", "x": outcome["point"][0],
                                 "y": outcome["point"][1], "button": step["button"],
                                 "duration_ms": step["duration_ms"]})
            else:
                resolved.append({"op": REFUSAL, "outcome": outcome})
        return resolved, records

    def validate(self, steps):
        rewritten = []
        mint_count = 0
        for step in steps:
            if not isinstance(step, dict) or step.get("op") not in (MINT, REFUSAL):
                rewritten.append(step)
                continue
            if step["op"] == MINT:
                required = {"op", "name", "coordinate_frame", "box", "ttl_ms",
                            "freshness_ms", "search_radius", "allowed_transformations"}
                if set(step) != required:
                    raise ValueError("invalid target-handle mint fields")
                mint_count += 1
            elif set(step) != {"op", "outcome"}:
                raise ValueError("invalid target-handle refusal fields")
            rewritten.append({"op": "observe"})
        if mint_count > 1:
            raise ValueError("at most one target handle may be minted per program")
        super().validate(rewritten)

    def execute(self, step, cancel, identifier, index):
        if step["op"] == MINT:
            now_ns = time.perf_counter_ns()
            record = self.handles.mint(
                step["name"], step["coordinate_frame"], step["box"],
                self.observation(), self.image(), now_ns, step["ttl_ms"],
                step["freshness_ms"], step["search_radius"],
                tuple(step["allowed_transformations"]))
            self.emit({"event": "target_handle_minted", "id": identifier,
                       "step": index, "minted_ns": now_ns, **record})
            self.snapshot(identifier, index)
            return record
        if step["op"] == REFUSAL:
            from executor_v3 import DecisionRequired
            self.emit({"event": "target_handle_refused", "id": identifier,
                       "step": index, **step["outcome"]})
            raise DecisionRequired("target handle " + step["outcome"]["status"])
        return super().execute(step, cancel, identifier, index)
