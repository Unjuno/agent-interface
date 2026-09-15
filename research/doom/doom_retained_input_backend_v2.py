"""Typed DOOM adapter for non-staggering input release telemetry v2."""
import threading

from doom_typed_coast_backend_v1 import Backend as Previous, suite
from input_transition_owner_v2 import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        self.owner.close()
        self.owner = InputOwner(session.name)
        self._release_batch = threading.local()

    def execute(self, step, cancel, identifier, index):
        previous = getattr(self._release_batch, "rows", None)
        self._release_batch.rows = []
        try:
            return super().execute(step, cancel, identifier, index)
        finally:
            # An incomplete batch means a release path raised. Never carry a
            # partial success receipt into the next executor step, and never
            # leave a fake step context installed after execution returns.
            if previous is None:
                try:
                    del self._release_batch.rows
                except AttributeError:
                    pass
            else:
                self._release_batch.rows = previous

    def raw(self, key, down):
        if down:
            record = self.owner.call("down", self.lease, key)
            self.held.add(key)
            if record is not None:
                self.emit(record)
            return None

        rows = getattr(self._release_batch, "rows", None)
        if rows is None:
            # Defensive non-step cleanup path: preserve release semantics but do
            # not fabricate a provenance-complete telemetry batch.
            self.owner.call("up", self.lease, key)
            self.held.discard(key)
            return None

        was_backend_owned = key in self.held
        record = self.owner.call("up", self.lease, key)
        self.held.discard(key)
        if not isinstance(record, dict) or record.get("event") != "input_release_transition":
            raise AssertionError("v2 release wrapper did not return transition receipt")
        record["backend_owned_before_release"] = was_backend_owned
        rows.append(record)

        # Critical v2 rule: no state query and no event publication while another
        # backend-held key remains. This keeps multi-key release order identical
        # to the historical release loop except for cheap monotonic timestamps.
        if self.held:
            return None

        after = self.owner.call("input_state")
        owned_after = list(after["owned_keycodes"])
        latest_release_return_ns = max(
            row["release_call_returned_ns"] for row in rows)
        sample_ordered = (
            type(after.get("sample_started_ns")) is int
            and type(after.get("sample_finished_ns")) is int
            and latest_release_return_ns <= after["sample_started_ns"]
            <= after["sample_finished_ns"]
        )
        owner_identity_matches = all(
            row.get("owner_id") == after.get("owner_id") for row in rows)
        batch_verified = (
            not owned_after
            and sample_ordered
            and owner_identity_matches
            and all(row.get("backend_owned_before_release") is True for row in rows)
            and all(row.get("ordinary_release_candidate") is True for row in rows)
        )
        batch_size = len(rows)
        for position, row in enumerate(rows):
            row.update({
                "release_batch_schema": "input-release-batch-v2",
                "release_batch_size": batch_size,
                "release_batch_position": position,
                "owner_sample_after_started_ns": after.get("sample_started_ns"),
                "owner_sample_after_finished_ns": after.get("sample_finished_ns"),
                "owner_sample_ordered_after_batch": sample_ordered,
                "owner_identity_matches_after_batch": owner_identity_matches,
                "owned_keycodes_after_batch": owned_after,
                "owned_count_after_batch": len(owned_after),
                "owner_transition_verified": batch_verified,
                "measurement_contract_v2": (
                    "all explicit key-up calls in this backend-held batch complete "
                    "before the single owner-state sample and before telemetry publication"
                ),
            })
        for row in rows:
            self.emit(row)
        rows.clear()
        return None
