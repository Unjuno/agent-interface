"""Cause-servo backend with one receipt-dependent target click operation."""
import copy
import time

from PIL import Image
from Xlib import X

from cause_servo_session_v1 import Backend as Previous, suite
from executor_v3 import DecisionRequired
from receipt_target_admission_v1 import evaluate, validate as validate_receipt


OPERATION = "pointer_click_receipt_target"
FOCUS_AWAY = "test_focus_away"
FOCUS_RESTORE = "test_focus_restore"


class Backend(Previous):
    def __init__(self, session, out, emit):
        super().__init__(session, out, emit)
        self.receipt_history = {}
        self.last_observation = None
        self.test_focus_original = None
        self.test_focus_sink = None

    def image(self):
        frame = self.decoder.frame
        if frame is None or frame.mode != "RGB":
            raise ValueError("RGB source observation required")
        return Image.frombytes(frame.mode, (frame.width, frame.height), frame.pixels)

    def snapshot(self, identifier, index):
        observations = []
        emit = self.emit

        def collect(record):
            if record.get("event") == "observation":
                observations.append(copy.deepcopy(record))
            emit(record)

        self.emit = collect
        try:
            result = super().snapshot(identifier, index)
        finally:
            self.emit = emit
        if not observations:
            raise RuntimeError("snapshot did not emit an observation")
        observation = observations[-1]
        self.last_observation = observation
        self.receipt_history[observation["sequence"]] = {
            "observation": observation, "image": self.image().copy()}
        while len(self.receipt_history) > 64:
            del self.receipt_history[next(iter(self.receipt_history))]
        return result

    def validate(self, steps):
        rewritten = []
        checked = 0
        for step in steps:
            if isinstance(step, dict) and step.get("op") in (FOCUS_AWAY, FOCUS_RESTORE):
                if set(step) != {"op"}:
                    raise ValueError("invalid test focus operation")
                rewritten.append({"op": "observe"})
                continue
            if not isinstance(step, dict) or step.get("op") != OPERATION:
                rewritten.append(step)
                continue
            if set(step) != {"op", "receipt", "button", "duration_ms"}:
                raise ValueError("invalid receipt-target click fields")
            validate_receipt(step["receipt"])
            if type(step["button"]) is not int or step["button"] not in (1, 2, 3):
                raise ValueError("button 1..3 required")
            if type(step["duration_ms"]) is not int or not 1 <= step["duration_ms"] <= 250:
                raise ValueError("duration_ms must be 1..250")
            checked += 1
            rewritten.append({"op": "pointer_click", "x": step["receipt"]["point"][0],
                              "y": step["receipt"]["point"][1],
                              "button": step["button"],
                              "duration_ms": step["duration_ms"]})
        if checked > 1:
            raise ValueError("at most one receipt-target click per program")
        super().validate(rewritten)

    def execute(self, step, cancel, identifier, index):
        if step["op"] == FOCUS_AWAY:
            if self.test_focus_sink is not None:
                raise ValueError("test focus fault already active")
            original = self.session.d.get_input_focus().focus
            self.test_focus_original = original.id if hasattr(original, "id") else original
            root = self.session.d.screen().root
            sink = root.create_window(5, 5, 96, 48, 0, self.session.d.screen().root_depth,
                                      X.InputOutput, X.CopyFromParent)
            sink.set_wm_name("Agent Interface receipt focus fault")
            sink.map()
            sink.set_input_focus(X.RevertToParent, X.CurrentTime)
            self.session.d.sync()
            self.test_focus_sink = sink
            self.emit({"event": "test_focus_changed", "id": identifier,
                       "step": index, "original_focus": self.test_focus_original,
                       "fault_focus": sink.id,
                       "authority": "fault injection only; grants no input authority"})
            return
        if step["op"] == FOCUS_RESTORE:
            if self.test_focus_sink is None or self.test_focus_original in (None, 0, 1):
                raise ValueError("test focus fault is not active")
            original = self.session.d.create_resource_object("window", self.test_focus_original)
            original.set_input_focus(X.RevertToParent, X.CurrentTime)
            self.test_focus_sink.destroy()
            self.session.d.sync()
            self.emit({"event": "test_focus_restored", "id": identifier,
                       "step": index, "focus": self.test_focus_original,
                       "authority": "fault cleanup only; grants no input authority"})
            self.test_focus_sink = None
            self.test_focus_original = None
            return
        if step["op"] != OPERATION:
            return super().execute(step, cancel, identifier, index)
        retained = copy.copy(self.receipt_history)
        self.snapshot(identifier, index)
        current = self.last_observation
        now_ns = time.perf_counter_ns()
        outcome = evaluate(step["receipt"], retained, current, self.image(), now_ns)
        checked_ns = time.perf_counter_ns()
        self.emit({"event": "receipt_target_revalidated", "id": identifier,
                   "step": index, "checked_ns": checked_ns, **outcome})
        if not outcome["eligible"]:
            self.emit({"event": "receipt_target_refused", "id": identifier,
                       "step": index, "checked_ns": checked_ns, **outcome})
            raise DecisionRequired("receipt target " + outcome["reason"])
        if checked_ns >= outcome["valid_until_ns"]:
            raise DecisionRequired("receipt target expired before input adapter")
        result = super().execute({"op": "pointer_click", "x": outcome["point"][0],
                                  "y": outcome["point"][1],
                                  "button": step["button"],
                                  "duration_ms": step["duration_ms"]},
                                 cancel, identifier, index)
        self.emit({"event": "receipt_target_dispatched", "id": identifier,
                   "step": index, "checked_ns": checked_ns,
                   "valid_until_ns": outcome["valid_until_ns"],
                   "authority_class": outcome["authority_class"]})
        return result

    def close(self):
        if self.test_focus_sink is not None:
            try:
                if self.test_focus_original not in (None, 0, 1):
                    original = self.session.d.create_resource_object(
                        "window", self.test_focus_original)
                    original.set_input_focus(X.RevertToParent, X.CurrentTime)
                self.test_focus_sink.destroy()
                self.session.d.sync()
            finally:
                self.test_focus_sink = None
                self.test_focus_original = None
        return super().close()
