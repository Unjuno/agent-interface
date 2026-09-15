"""DOOM typed backend with program-bound ordinary release RPC telemetry.

This is measurement-only.  It preserves the v1 backend semantics and replaces
only its InputOwner v10 instance with the v11 telemetry wrapper.  Keyboard
records are enriched with program/step provenance; pointer release receipts are
already emitted by the inherited session_v9 pointer helper with the same fields.
"""
from __future__ import annotations

from doom_typed_release_backend_v1 import Backend as Previous, suite
from input_owner_v11 import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        # V1 already replaced the construction owner before measured authority.
        # Replace that empty owner once more with the telemetry-only v11 wrapper.
        self.owner.close()
        self.owner = InputOwner(session.name)
        self._input_event_context = None

    def execute(self, step, cancel, identifier, index):
        if self._input_event_context is not None:
            raise RuntimeError("nested input telemetry context")
        self._input_event_context = (identifier, index)
        try:
            return super().execute(step, cancel, identifier, index)
        finally:
            self._input_event_context = None

    def raw(self, key, down):
        operation = "down" if down else "up"
        record = self.owner.call(operation, self.lease, key)
        if down:
            self.held.add(key)
        else:
            self.held.discard(key)
        if record is None:
            return

        row = dict(record)
        context = self._input_event_context
        if context is None:
            # Input without executor step provenance is a measurement contract
            # violation in this version; do not silently publish an unbound edge.
            raise RuntimeError("keyboard input outside program/step telemetry context")
        row["id"], row["step"] = context
        row.setdefault("owner_id", self.owner.owner_id)
        row.setdefault("intent_token", getattr(self.lease, "intent_token", None))
        self.emit(row)
