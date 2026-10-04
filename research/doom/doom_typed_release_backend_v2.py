"""DOOM typed backend with program-bound ordinary release RPC telemetry.

This is measurement-only.  It preserves the v1 backend semantics and replaces
only its InputOwner v10 instance with the v11 telemetry wrapper.  Keyboard
records are enriched with program/step provenance; pointer release receipts are
already emitted by the inherited session_v9 pointer helper with the same fields.
"""
from __future__ import annotations

import time

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
        context = self._input_event_context
        if context is None:
            # Reject before touching the owner. A measurement build must never
            # create an OS-input edge that cannot be attributed to a program step.
            raise RuntimeError("keyboard input outside program/step telemetry context")

        operation = "down" if down else "up"
        call_started_ns = time.perf_counter_ns()
        try:
            record = self.owner.call(operation, self.lease, key)
        except Exception as exc:
            call_returned_ns = time.perf_counter_ns()
            if not down:
                self.emit({
                    "event": "input_release_rpc_error",
                    "operation": operation,
                    "payload": key,
                    "owner_id": self.owner.owner_id,
                    "intent_token": getattr(self.lease, "intent_token", None),
                    "call_started_ns": call_started_ns,
                    "call_returned_ns": call_returned_ns,
                    "call_interval_ns": [call_started_ns, call_returned_ns],
                    "outcome_uncertain": True,
                    "error_type": type(exc).__name__,
                    "grants_input_authority": False,
                    "continuous_physical_state_sampled": False,
                    "application_consumption_observed": False,
                    "id": context[0],
                    "step": context[1],
                })
            raise
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
