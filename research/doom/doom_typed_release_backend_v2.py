"""DOOM typed backend with telemetry-only ordinary key-release edge receipts.

This version preserves InputOwner v10 authority/release semantics.  It adds only:
- caller-side monotonic brackets around ordinary ``owner.call('up', ...)``;
- one post-batch X11 ``query_keymap`` sample after the final key of a release
  batch has returned from InputOwner.

The sample is X-server state, not hardware state, and the caller-side return is
known to be after InputOwner's internal ``d.sync()`` but is not relabelled as the
exact internal sync timestamp.
"""
from __future__ import annotations

import threading
import time

from Xlib import XK, display

from doom_typed_release_backend_v1 import Backend as Previous, suite
from release_edge_telemetry_v1 import finalize_release_batch, time_release_call


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        # Dedicated read-only X11 connection so key-state sampling does not share
        # the session capture connection or the InputOwner injection connection.
        self._release_telemetry_display = display.Display(session.name)
        self._release_telemetry_lock = threading.Lock()
        self._release_telemetry_context = threading.local()

    def execute(self, step, cancel, identifier, index):
        previous = getattr(self._release_telemetry_context, "value", None)
        self._release_telemetry_context.value = {
            "id": identifier,
            "step": index,
            "releases": [],
        }
        try:
            return super().execute(step, cancel, identifier, index)
        finally:
            if previous is None:
                try:
                    del self._release_telemetry_context.value
                except AttributeError:
                    pass
            else:
                self._release_telemetry_context.value = previous

    def _sample_released_keys(self, keys):
        with self._release_telemetry_lock:
            keycodes = {}
            for key in keys:
                code = self._release_telemetry_display.keysym_to_keycode(
                    XK.string_to_keysym(key))
                if not code:
                    raise ValueError("key unavailable on telemetry display: " + repr(key))
                keycodes[key] = code

            def sample_bitmap():
                return self._release_telemetry_display.query_keymap()

            return finalize_release_batch(
                self._release_telemetry_context.value["releases"],
                sample_bitmap,
                keycodes,
                time.perf_counter_ns,
            )

    def raw(self, key, down):
        if down:
            return super().raw(key, down)

        context = getattr(self._release_telemetry_context, "value", None)
        if context is None:
            # Defensive fallback for any cleanup path outside executor step
            # context. Preserve inherited semantics without inventing provenance.
            return super().raw(key, down)

        receipt = time_release_call(
            key,
            lambda: self.owner.call("up", self.lease, key),
            time.perf_counter_ns,
        )
        self.held.discard(key)
        context["releases"].append(receipt)

        # Do not query/log between releases of a multi-key chord. Only after the
        # final backend-held key is released do we add one state sample/event.
        if self.held:
            return None

        batch = self._sample_released_keys(
            [row["key"] for row in context["releases"]])
        self.emit({
            "event": "ordinary_release_telemetry",
            "id": context["id"],
            "step": context["step"],
            **batch,
        })
        context["releases"].clear()
        return None

    def close(self):
        try:
            return super().close()
        finally:
            self._release_telemetry_display.close()
