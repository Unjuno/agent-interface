"""Capture one fresh observation and resolve one read-only target alias on it."""
from observe_target_handle_v1 import OPERATION, execute, validate_step
from session_v31 import Backend as Previous, suite


OBSERVE_TARGET = OPERATION


class Backend(Previous):
    def validate(self, steps):
        rewritten = []
        combined = 0
        for step in steps:
            if not isinstance(step, dict) or step.get("op") != OBSERVE_TARGET:
                rewritten.append(step)
                continue
            validate_step(step)
            combined += 1
            rewritten.append({"op": "observe"})
        if combined > 1:
            raise ValueError("at most one observe-target step per program")
        super().validate(rewritten)

    def execute(self, step, cancel, identifier, index):
        if step["op"] != OBSERVE_TARGET:
            return super().execute(step, cancel, identifier, index)
        return execute(self, step, identifier, index)
