"""Fault-only backend for a post-admission surface-geometry change."""
import time

from session_v26 import Backend as Previous, suite


class Backend(Previous):
    def validate(self, steps):
        faults = 0
        rewritten = []
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
            if index + 1 >= len(steps):
                raise ValueError("test surface move must precede another step")
            faults += 1
            rewritten.append({"op": "observe"})
        if faults != 1:
            raise ValueError("exactly one test surface move required")
        super().validate(rewritten)

    def execute(self, step, cancel, identifier, index):
        if step["op"] != "test_move_surface":
            return super().execute(step, cancel, identifier, index)
        if not hasattr(cancel, "expected_focus"):
            cancel.expected_focus = self.observed_focus
            binding = self.observed_pointer
            cancel.expected_surface = binding["surface"] if binding else None
            cancel.expected_geometry = list(binding["geometry"]) if binding else None
        before = self.binding()
        if before["surface"] != cancel.expected_surface or before["geometry"] != cancel.expected_geometry:
            raise ValueError("surface changed before fault injection")
        window = self.session.d.create_resource_object("window", before["surface"])
        target_x = before["geometry"][0] + step["dx"]
        target_y = before["geometry"][1] + step["dy"]
        window.configure(x=target_x, y=target_y)
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
