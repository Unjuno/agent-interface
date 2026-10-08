"""Successor measurement bridge for cancellation-owned per-key releases."""
from map01_v39_perkey_bridge_a01.bridge import Backend as Previous
from input_owner_v13_candidate import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        self.owner.close()
        self.owner = InputOwner(session.name)
        self._input_event_context = None
        self._owner_record_cursor = len(self.owner.records)

    def execute(self, step, cancel, identifier, index):
        try:
            return super().execute(step, cancel, identifier, index)
        finally:
            try:
                if self.lease.cancel.is_set():
                    # This owner-thread request is ordered after cancellation cleanup.
                    state = self.owner.call("input_state", self.lease)
                    if state.get("owned_keycodes") == [] and state.get("owned_buttons") == []:
                        self.held.clear()
            finally:
                # Owner cleanup also occurs on expiry and other exits that do
                # not set the cancellation event. Always preserve rows already
                # recorded before execute returns or raises.
                self._drain_owner_records()

    def _drain_owner_records(self):
        records = self.owner.records
        while self._owner_record_cursor < len(records):
            record = records[self._owner_record_cursor]
            self._owner_record_cursor += 1
            if record.get("event") != "owner_release":
                continue
            for row in record.get("per_key_release_measurements", []):
                self.emit(dict(row))
                measurement = row.get("physical_key_measurement", {})
                if measurement.get("classification") == "CONFIRMED_PHYSICAL_UP":
                    self.held.discard(row.get("key"))
            if (record.get("verified") is True and record.get("keys_down") == []
                    and record.get("buttons_down") == []):
                self.held.clear()

    def release_all(self):
        try:
            return super().release_all()
        finally:
            # Executor terminal cleanup runs after execute() has returned.
            # Drain again after that ordered owner barrier so cleanup that was
            # still pending at the execute boundary is not stranded.
            self._drain_owner_records()

    def raw(self, key, down):
        context = self._input_event_context
        if context is None:
            raise RuntimeError("keyboard input outside program/step telemetry context")
        operation = "down" if down else "up"
        record = self.owner.call(operation, self.lease, key, event_context=context)
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
