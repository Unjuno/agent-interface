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
        self._pending_owner_record_indices = set()
        self._emitted_owner_release_rows = set()

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
        indices = sorted(self._pending_owner_record_indices)
        self._pending_owner_record_indices.clear()
        indices.extend(range(self._owner_record_cursor, len(records)))
        self._owner_record_cursor = len(records)
        for index in indices:
            if index >= len(records):
                continue
            record = records[index]
            if record.get("event") != "owner_release":
                continue
            for row_index, row in enumerate(record.get("per_key_release_measurements", [])):
                row_key = (index, row_index)
                if row_key not in self._emitted_owner_release_rows:
                    self.emit(dict(row))
                    self._emitted_owner_release_rows.add(row_key)
                measurement = row.get("physical_key_measurement", {})
                if measurement.get("classification") == "CONFIRMED_PHYSICAL_UP":
                    self.held.discard(row.get("key"))
            verified_empty = (
                record.get("verified") is True
                and record.get("keys_down") == []
                and record.get("buttons_down") == []
            )
            if verified_empty:
                self.held.clear()
            else:
                self._pending_owner_record_indices.add(index)

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
        measurement = row.get("physical_key_measurement", {})
        if not down and measurement.get("classification") == "NOOP_ALREADY_UP":
            # Diagnostic evidence after owner cleanup is not a second edge.
            row["event"] = "input_release_noop"
        row["id"], row["step"] = context
        row.setdefault("owner_id", self.owner.owner_id)
        row.setdefault("intent_token", getattr(self.lease, "intent_token", None))
        self.emit(row)

    def release_all(self):
        try:
            release = self.owner.call("release", self.lease)
        finally:
            # Executor calls this after execute() returns. Expiry cleanup may
            # race its earlier exit drain, so drain again at the release barrier.
            self._drain_owner_records()
        state = self.owner.call("input_state", self.lease)
        verified = (release.get("verified") is True
                    and state.get("owned_keycodes") == []
                    and state.get("owned_buttons") == [])
        if verified:
            self.held.clear()
        return {"verified": verified, "owner_id": self.owner.owner_id}
