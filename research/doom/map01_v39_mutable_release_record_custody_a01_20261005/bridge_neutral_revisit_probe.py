"""Diagnostic-only bridge probe: revisit monotonic aggregate-neutral state."""
from bridge_v2_candidate import Backend as FrozenBackend


class Backend(FrozenBackend):
    def _drain_owner_records(self):
        records = self.owner.records
        counts = getattr(self, "_probe_emitted_row_counts", None)
        if counts is None:
            counts = self._probe_emitted_row_counts = []
        while len(counts) < len(records):
            counts.append(0)
        for index, record in enumerate(records):
            rows = record.get("per_key_release_measurements", [])
            while counts[index] < len(rows):
                row = rows[counts[index]]
                self.emit(dict(row))
                measurement = row.get("physical_key_measurement", {})
                if measurement.get("classification") == "CONFIRMED_PHYSICAL_UP":
                    self.held.discard(row.get("key"))
                counts[index] += 1
            if (record.get("event") == "owner_release"
                    and record.get("verified") is True
                    and record.get("keys_down") == []
                    and record.get("buttons_down") == []):
                self.held.clear()
        self._owner_record_cursor = len(records)
