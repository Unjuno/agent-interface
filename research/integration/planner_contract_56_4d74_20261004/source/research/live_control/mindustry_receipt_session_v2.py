"""Fault controls for unavailable binding and live resize receipt checks."""
import time

from Xlib import X, error, protocol

from mindustry_receipt_session_v1 import Backend as Previous, suite
from executor_v3 import DecisionRequired


FOCUS_UNBOUND = "test_focus_unbound"
FOCUS_UNBOUND_RESTORE = "test_focus_unbound_restore"
SURFACE_RESIZE = "test_surface_resize"
SURFACE_RESIZE_RESTORE = "test_surface_resize_restore"


class Backend(Previous):
    def __init__(self, session, out, emit):
        super().__init__(session, out, emit)
        self.test_unbound_original = None
        self.test_unbound_sink = None
        self.test_resize_original = None
        self.test_resize_was_maximized = False

    def validate(self, steps):
        rewritten = []
        fault_counts = {FOCUS_UNBOUND: 0, FOCUS_UNBOUND_RESTORE: 0,
                        SURFACE_RESIZE: 0, SURFACE_RESIZE_RESTORE: 0}
        for step in steps:
            if not isinstance(step, dict) or step.get("op") not in fault_counts:
                rewritten.append(step)
                continue
            op = step["op"]
            if op == SURFACE_RESIZE:
                if set(step) != {"op", "width_delta"}:
                    raise ValueError("invalid test surface resize fields")
                if (type(step["width_delta"]) is not int or
                        not -128 <= step["width_delta"] <= 128 or
                        step["width_delta"] == 0):
                    raise ValueError("bounded nonzero width delta required")
            elif set(step) != {"op"}:
                raise ValueError("invalid test fault fields")
            fault_counts[op] += 1
            rewritten.append({"op": "observe"})
        if any(count > 1 for count in fault_counts.values()):
            raise ValueError("each test fault operation may occur at most once")
        super().validate(rewritten)

    def _wait_binding(self, predicate, message):
        deadline = time.monotonic() + 3
        current = self.binding()
        while not predicate(current) and time.monotonic() < deadline:
            time.sleep(.01)
            current = self.binding()
        if not predicate(current):
            raise RuntimeError(message)
        return current

    def _maximized(self, window):
        state = self.session.d.intern_atom("_NET_WM_STATE")
        horizontal = self.session.d.intern_atom("_NET_WM_STATE_MAXIMIZED_HORZ")
        vertical = self.session.d.intern_atom("_NET_WM_STATE_MAXIMIZED_VERT")
        prop = window.get_full_property(state, X.AnyPropertyType)
        values = set(prop.value) if prop is not None else set()
        return horizontal in values and vertical in values

    def _set_maximized(self, window, enabled):
        state = self.session.d.intern_atom("_NET_WM_STATE")
        horizontal = self.session.d.intern_atom("_NET_WM_STATE_MAXIMIZED_HORZ")
        vertical = self.session.d.intern_atom("_NET_WM_STATE_MAXIMIZED_VERT")
        event = protocol.event.ClientMessage(
            window=window, client_type=state,
            data=(32, [1 if enabled else 0, horizontal, vertical, 1, 0]))
        self.session.d.screen().root.send_event(
            event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
        self.session.d.sync()

    def execute(self, step, cancel, identifier, index):
        op = step["op"]
        if op == FOCUS_UNBOUND:
            if self.test_unbound_original is not None:
                raise ValueError("unbound focus fault already active")
            focus = self.session.d.get_input_focus().focus
            original = focus.id if hasattr(focus, "id") else focus
            if original in (None, 0, 1):
                raise DecisionRequired("usable focus unavailable before fault")
            root = self.session.d.screen().root
            sink = root.create_window(
                3, 3, 2, 2, 0, 0, X.InputOnly, X.CopyFromParent,
                override_redirect=1)
            sink.map()
            self.test_unbound_original = original
            self.test_unbound_sink = sink
            sink.set_input_focus(X.RevertToParent, X.CurrentTime)
            self.session.d.sync()
            after = self._wait_binding(
                lambda value: value["surface"] is None,
                "test focus did not produce unavailable pointer binding")
            self.emit({"event": "test_focus_unbound", "id": identifier,
                       "step": index, "original_focus": original,
                       "fault_focus": sink.id, "after": after,
                       "authority": "fault injection only; grants no input authority"})
            return
        if op == FOCUS_UNBOUND_RESTORE:
            if self.test_unbound_original in (None, 0, 1):
                raise ValueError("unbound focus fault is not active")
            original = self.session.d.create_resource_object(
                "window", self.test_unbound_original)
            original.set_input_focus(X.RevertToParent, X.CurrentTime)
            if self.test_unbound_sink is not None:
                self.test_unbound_sink.destroy()
            self.session.d.sync()
            restored = self._wait_binding(
                lambda value: value["focus"] == self.test_unbound_original and
                              value["surface"] is not None,
                "test focus did not restore")
            self.emit({"event": "test_focus_unbound_restored", "id": identifier,
                       "step": index, "restored": restored,
                       "authority": "fault cleanup only; grants no input authority"})
            self.test_unbound_original = None
            self.test_unbound_sink = None
            return
        if op == SURFACE_RESIZE:
            if self.test_resize_original is not None:
                raise ValueError("surface resize fault already active")
            before = self.binding()
            if before["surface"] is None or before["geometry"] is None:
                raise DecisionRequired("surface unavailable before resize fault")
            target_width = before["geometry"][2] + step["width_delta"]
            if target_width < 320:
                raise ValueError("test surface width would be too small")
            self.test_resize_original = before
            window = self.session.d.create_resource_object("window", before["surface"])
            self.test_resize_was_maximized = self._maximized(window)
            if self.test_resize_was_maximized:
                self._set_maximized(window, False)
                self._wait_binding(
                    lambda value: value["surface"] == before["surface"] and
                                  value["geometry"] != before["geometry"],
                    "test surface did not leave maximized geometry")
            window.configure(width=target_width)
            self.session.d.sync()
            after = self._wait_binding(
                lambda value: value["surface"] == before["surface"] and
                              value["geometry"][2] == target_width,
                "test surface did not resize")
            self.emit({"event": "test_surface_resized", "id": identifier,
                       "step": index, "before": before, "after": after,
                       "authority": "fault injection only; grants no input authority"})
            return
        if op == SURFACE_RESIZE_RESTORE:
            if self.test_resize_original is None:
                raise ValueError("surface resize fault is not active")
            before = self.test_resize_original
            current = self.binding()
            window = self.session.d.create_resource_object("window", before["surface"])
            window.configure(x=before["geometry"][0], y=before["geometry"][1],
                             width=before["geometry"][2], height=before["geometry"][3])
            if self.test_resize_was_maximized:
                self._set_maximized(window, True)
            self.session.d.sync()
            restored = self._wait_binding(
                lambda value: value["surface"] == before["surface"] and
                              value["geometry"] == before["geometry"],
                "test surface geometry did not restore")
            self.emit({"event": "test_surface_resize_restored", "id": identifier,
                       "step": index, "changed": current, "restored": restored,
                       "authority": "fault cleanup only; grants no input authority"})
            self.test_resize_original = None
            self.test_resize_was_maximized = False
            return
        return super().execute(step, cancel, identifier, index)

    def close(self):
        try:
            if self.test_unbound_original not in (None, 0, 1):
                original = self.session.d.create_resource_object(
                    "window", self.test_unbound_original)
                original.set_input_focus(X.RevertToParent, X.CurrentTime)
                if self.test_unbound_sink is not None:
                    self.test_unbound_sink.destroy()
                self.session.d.sync()
            if self.test_resize_original is not None:
                before = self.test_resize_original
                window = self.session.d.create_resource_object("window", before["surface"])
                window.configure(x=before["geometry"][0], y=before["geometry"][1],
                                 width=before["geometry"][2], height=before["geometry"][3])
                if self.test_resize_was_maximized:
                    self._set_maximized(window, True)
                self.session.d.sync()
        except (error.BadWindow, error.BadDrawable):
            pass
        finally:
            self.test_unbound_original = None
            self.test_unbound_sink = None
            self.test_resize_original = None
            self.test_resize_was_maximized = False
        return super().close()
