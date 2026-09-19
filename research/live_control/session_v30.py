"""Read-only target-handle query before model choice; admission still revalidates."""
import time

from session_v29 import Backend as Previous, suite


QUERY = "target_handle_query"


class Backend(Previous):
    def validate(self, steps):
        rewritten = []
        queries = 0
        for step in steps:
            if not isinstance(step, dict) or step.get("op") != QUERY:
                rewritten.append(step)
                continue
            if set(step) != {"op", "target_handle", "offset"}:
                raise ValueError("invalid target-handle query fields")
            if (type(step["offset"]) is not list or len(step["offset"]) != 2
                    or any(type(value) is not int for value in step["offset"])):
                raise ValueError("target-handle query offset must be two integers")
            queries += 1
            rewritten.append({"op": "observe"})
        if queries > 1:
            raise ValueError("at most one target-handle query per program")
        super().validate(rewritten)

    def execute(self, step, cancel, identifier, index):
        if step["op"] != QUERY:
            return super().execute(step, cancel, identifier, index)
        checked_ns = time.perf_counter_ns()
        outcome = self.handles.resolve_point(
            step["target_handle"], step["offset"], self.observation(), self.image(),
            checked_ns, session_scope="x11:" + self.session.name
        )
        record = {
            "event": "target_handle_checked",
            "id": identifier,
            "step": index,
            "checked_ns": checked_ns,
            "authority": "observation only; grants no input authority",
            **outcome,
        }
        self.emit(record)
        self.snapshot(identifier, index)
        return outcome
