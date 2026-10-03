"""Fault-only extension: optional bounded surface move between handle uses."""
import time

from executor_v3 import DecisionRequired
from session_v28 import Backend as Previous, suite


class Backend(Previous):
    def validate(self, steps):
        rewritten = []
        faults = 0
        for index, step in enumerate(steps):
            if not isinstance(step, dict) or step.get("op") != "test_move_surface":
                rewritten.append(step)
                continue
            if set(step) != {"op", "dx", "dy"}:
                raise ValueError("invalid test_move_surface fields")
            if any(type(step[key]) is not int or abs(step[key]) > 64 for key in ("dx", "dy")):
                raise ValueError("test surface delta must be bounded integers")
            if step["dx"] == 0 and step["dy"] == 0:
                raise ValueError("test surface delta must change geometry")
            faults += 1
            rewritten.append({"op": "observe"})
        if faults > 1:
            raise ValueError("at most one test surface move allowed")
        super().validate(rewritten)

    def execute(self, step, cancel, identifier, index):
        if step["op"] != "test_move_surface":
            return super().execute(step, cancel, identifier, index)
        before = self.binding()
        if before["surface"] is None:
            raise DecisionRequired("surface unavailable before fault injection")
        window = self.session.d.create_resource_object("window", before["surface"])
        window.configure(x=before["geometry"][0] + step["dx"],
                         y=before["geometry"][1] + step["dy"])
        self.session.d.sync()
        deadline = time.monotonic() + 2
        after = self.binding()
        while after["geometry"] == before["geometry"] and time.monotonic() < deadline:
            time.sleep(.01)
            after = self.binding()
        if after["geometry"] == before["geometry"]:
            raise RuntimeError("test surface did not move")
        self.emit({"event": "test_surface_moved", "id": identifier, "step": index,
                   "before": before, "after": after,
                   "authority": "fault injection only; grants no input authority"})
