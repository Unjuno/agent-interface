"""Measurement-only v39 backend bridge to InputOwner v12 per-key evidence."""
from __future__ import annotations

from doom_typed_release_backend_v1 import Backend as Previous, suite
from input_owner_v12 import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
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
        context = self._input_event_context
        if context is None:
            raise RuntimeError("keyboard input outside program/step telemetry context")

        operation = "down" if down else "up"
        record = self.owner.call(operation, self.lease, key)
        if down:
            self.held.add(key)
        else:
            self.held.discard(key)
        if record is None:
            return

        row = dict(record)
        row["id"], row["step"] = context
        row.setdefault("owner_id", self.owner.owner_id)
        row.setdefault("intent_token", getattr(self.lease, "intent_token", None))
        self.emit(row)
