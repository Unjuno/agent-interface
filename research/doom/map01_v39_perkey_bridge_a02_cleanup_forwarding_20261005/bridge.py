"""Measurement-only v39 bridge with asynchronous owner cleanup forwarding."""
from __future__ import annotations

from doom_typed_release_backend_v1 import Backend as Previous, suite
from input_owner_v13 import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        self.owner.close()
        self.owner = InputOwner(session.name)
        self._input_event_context = None
        self._owner_records_cursor = 0
        self._active_actuations = {}
        self._actuation_context = {}

    def _emit_owner_cleanup(self, record):
        if record.get("event") != "owner_release":
            return
        for measurement in record.get("per_key_release_measurements", []):
            aid = measurement.get("actuation_id")
            bracket = measurement.get("bracket") or {}
            context = self._actuation_context.get(aid)
            key = measurement.get("key") or bracket.get("key")
            if context is None or not aid or not key:
                self.emit({"event": "input_cleanup_unscoped", "owner_cleanup_record": record,
                           "measurement": measurement, "grants_input_authority": False})
                continue
            interval = bracket.get("physical_up_interval")
            adapter_edge = None
            if (measurement.get("classification") == "CONFIRMED_PHYSICAL_UP"
                    and type(interval) is list and len(interval) == 2
                    and all(type(value) is int for value in interval)
                    and interval[0] <= interval[1]):
                adapter_edge = {"edge": "up", "status": "CONFIRMED_PHYSICAL_UP",
                                "actuation_id": aid, "owner_id": bracket.get("owner_id"),
                                "intent_token": bracket.get("intent_token"), "key": key,
                                "interval": interval, "grants_input_authority": False}
            event = {"event": "input_release_measurement", "id": context[0],
                     "step": context[1], "owner_id": bracket.get("owner_id"),
                     "intent_token": bracket.get("intent_token"), "key": key,
                     "physical_key_measurement": dict(measurement, adapter_edge=adapter_edge),
                     "owner_cleanup_record": record, "grants_input_authority": False,
                     "application_consumption_observed": False}
            self.emit(event)
            self._active_actuations.pop((bracket.get("owner_id"),
                                         bracket.get("intent_token"), key), None)
            self._actuation_context.pop(aid, None)

    def drain_owner_records(self):
        records = self.owner.records
        while self._owner_records_cursor < len(records):
            record = records[self._owner_records_cursor]
            self._owner_records_cursor += 1
            self._emit_owner_cleanup(record)

    def execute(self, step, cancel, identifier, index):
        if self._input_event_context is not None:
            raise RuntimeError("nested input telemetry context")
        self._input_event_context = (identifier, index)
        try:
            return super().execute(step, cancel, identifier, index)
        finally:
            self.drain_owner_records()
            self._input_event_context = None

    def raw(self, key, down):
        context = self._input_event_context
        if context is None:
            raise RuntimeError("keyboard input outside program/step telemetry context")
        self.drain_owner_records()
        operation = "down" if down else "up"
        record = self.owner.call(operation, self.lease, key)
        # A concurrent cancellation can publish the matching cleanup row before
        # call("down") returns. Register and emit the admission before draining it.
        if not (down and record is not None):
            self.drain_owner_records()
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
        measurement = row.get("physical_key_measurement", {})
        aid = measurement.get("actuation_id")
        bracket = measurement.get("bracket") or {}
        if down and aid:
            self._active_actuations[(row.get("owner_id"), row.get("intent_token"), key)] = aid
            self._actuation_context[aid] = context
        if not down and measurement.get("classification") == "NOOP_ALREADY_UP":
            # The asynchronous cleanup row, if any, is the sole release receipt.
            if (row.get("owner_id"), row.get("intent_token"), key) not in self._active_actuations:
                return
        self.emit(row)
        if down:
            self.drain_owner_records()

    def close(self):
        self.drain_owner_records()
        try:
            return super().close()
        finally:
            self.drain_owner_records()
