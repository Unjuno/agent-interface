"""Typed DOOM adapter for fail-closed non-staggering release telemetry v3."""
import threading

from doom_typed_release_backend_v1 import Backend as Previous, suite
from input_transition_owner_v3 import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        self.owner.close()
        self.owner = InputOwner(session.name)
        self._release_batch = threading.local()

    def execute(self, step, cancel, identifier, index):
        previous = getattr(self._release_batch, "context", None)
        if previous is not None and previous.get("identifier") == identifier:
            context = previous
        else:
            # A new program cannot inherit incomplete telemetry from the prior
            # program: its eventual sample would no longer bound that release batch.
            context = {"rows": [], "identifier": identifier}
        context["step"] = index
        self._release_batch.context = context
        try:
            result = super().execute(step, cancel, identifier, index)
        except BaseException:
            # Partial receipts from an exception/interruption are invalid and
            # must not leak into the next step/program.
            context["rows"].clear()
            try:
                del self._release_batch.context
            except AttributeError:
                pass
            raise

        # Keep an incomplete release batch across successful steps of the same
        # program. raw() clears rows only after the final held key is released,
        # owner state is sampled, and the receipts are published.
        if context["rows"]:
            self._release_batch.context = context
        else:
            try:
                del self._release_batch.context
            except AttributeError:
                pass
        return result

    def release_all(self):
        result = super().release_all()
        context = getattr(self._release_batch, "context", None)
        if context is not None and context["rows"]:
            cleanup_verified = isinstance(result, dict) and result.get("verified") is True
            self._publish_release_batch(
                context, terminal_cleanup_verified=cleanup_verified
            )
            try:
                del self._release_batch.context
            except AttributeError:
                pass
        return result

    def raw(self, key, down):
        if down:
            record = self.owner.call("down", self.lease, key)
            self.held.add(key)
            if record is not None:
                self.emit(record)
            return None

        context = getattr(self._release_batch, "context", None)
        if context is None:
            # Defensive non-step cleanup: preserve release semantics without
            # fabricating a provenance-complete normal-release measurement.
            self.owner.call("up", self.lease, key)
            self.held.discard(key)
            return None

        was_backend_owned = key in self.held
        records = getattr(self.owner, "records", None)
        record_count = len(records) if isinstance(records, list) else None
        row = self.owner.call("up", self.lease, key)
        self.held.discard(key)
        if not isinstance(row, dict) or row.get("event") != "input_release_transition":
            raise AssertionError("v3 release wrapper did not return transition receipt")
        row = dict(row)
        row["backend_owned_before_release"] = was_backend_owned
        row["release_batch_identifier"] = context["identifier"]
        row["release_batch_step"] = context["step"]
        row["owner_cleanup_record_count_before_release"] = (
            record_count
        )
        context["rows"].append(row)

        # Critical non-staggering invariant: do no sample and no publication
        # while another key in this logical backend-held batch remains.
        if self.held:
            return None

        self._publish_release_batch(context)
        return None

    def _publish_release_batch(self, context, *, terminal_cleanup_verified=None):
        rows = context["rows"]
        release_brackets_valid = [
            type(row.get("release_call_started_ns")) is int
            and type(row.get("release_call_returned_ns")) is int
            and row["release_call_started_ns"] <= row["release_call_returned_ns"]
            for row in rows
        ]
        latest_return_ns = (
            max(row["release_call_returned_ns"] for row in rows)
            if all(release_brackets_valid) else None
        )
        records = getattr(self.owner, "records", None)
        release_record_counts = [
            row.get("owner_cleanup_record_count_before_release") for row in rows
        ]
        valid_counts = (
            isinstance(records, list)
            and all(type(count) is int and 0 <= count <= len(records)
                    for count in release_record_counts)
        )
        first_count = min(release_record_counts) if valid_counts else None
        current_records = records[first_count:] if valid_counts else None
        after = self.owner.call("input_state")
        current_token = getattr(self.lease, "intent_token", None)
        sample_started_ns = after.get("sample_started_ns") if isinstance(after, dict) else None
        sample_finished_ns = after.get("sample_finished_ns") if isinstance(after, dict) else None
        sample_ordered = (
            type(sample_started_ns) is int
            and type(sample_finished_ns) is int
            and latest_return_ns is not None
            and latest_return_ns <= sample_started_ns <= sample_finished_ns
        )
        owner_id = after.get("owner_id") if isinstance(after, dict) else None
        owner_identity_matches = all(row.get("owner_id") == owner_id for row in rows)
        token_matches = all(row.get("intent_token") == current_token for row in rows)
        owned_after = after.get("owned_keycodes") if isinstance(after, dict) else None
        owner_empty = owned_after == []
        backend_ownership = all(row.get("backend_owned_before_release") is True for row in rows)
        ordinary = all(row.get("ordinary_release_candidate") is True for row in rows)
        owner_records = current_records
        cleanup_records_available = valid_counts
        cleanup_records_valid = cleanup_records_available
        if cleanup_records_available:
            for record in owner_records:
                if not isinstance(record, dict):
                    cleanup_records_valid = False
                    break
                event = record.get("event")
                if event == "owner_release":
                    cleanup_records_valid = (
                        type(record.get("verified_ns")) is int
                        and type(record.get("verified")) is bool
                        and record.get("verified") is True
                        and isinstance(record.get("keys_down"), list)
                        and not record["keys_down"]
                        and isinstance(record.get("buttons_down"), list)
                        and not record["buttons_down"]
                        and isinstance(record.get("reason"), str)
                        and (
                            record.get("valid_until_ns") is None
                            or type(record.get("valid_until_ns")) is int
                        )
                    )
                    if not cleanup_records_valid:
                        break
                elif event in ("owner_failed", "cleanup_failed"):
                    cleanup_records_valid = False
                    break
                else:
                    cleanup_records_valid = False
                    break
        cleanup_overlaps = []
        for row, bracket_valid in zip(rows, release_brackets_valid):
            started = row.get("release_call_started_ns")
            returned = row.get("release_call_returned_ns")
            overlaps = False
            if cleanup_records_available and bracket_valid:
                overlaps = any(
                    isinstance(record, dict)
                    and record.get("event") == "owner_release"
                    and type(record.get("verified_ns")) is int
                    and type(started) is int
                    and type(returned) is int
                    and started <= record["verified_ns"] <= returned
                    for record in owner_records
                )
            cleanup_overlaps.append(overlaps)
            row["owner_cleanup_records_available"] = cleanup_records_available
            row["owner_cleanup_records_valid"] = cleanup_records_valid
            row["owner_cleanup_overlapped_release_call"] = overlaps
            row["release_call_bracket_valid"] = bracket_valid
            if overlaps or not cleanup_records_valid or not bracket_valid:
                # A queued explicit up can arrive after cancellation cleanup has
                # already released the key. Do not classify that as an ordinary
                # per-key release, even if the wrapper's pre-call lease snapshot
                # was still ordinary.
                row["ordinary_release_candidate"] = False
        ordinary = (
            ordinary and cleanup_records_valid and all(release_brackets_valid)
            and not any(cleanup_overlaps)
        )
        cleanup_ok = terminal_cleanup_verified is not False
        if terminal_cleanup_verified is True:
            cleanup_ok = cleanup_ok and cleanup_records_valid and any(
                isinstance(record, dict)
                and record.get("event") == "owner_release"
                and record.get("reason") in (
                    "release", "cancelled", "stop_requested", "thread_exit"
                )
                and record.get("verified") is True
                and type(record.get("verified_ns")) is int
                for record in (owner_records or [])
            )
        batch_verified = bool(
            rows and cleanup_ok and sample_ordered and owner_identity_matches and token_matches
            and owner_empty and backend_ownership and ordinary
        )
        batch_size = len(rows)
        for position, receipt in enumerate(rows):
            receipt.update({
                "release_batch_schema": "input-release-batch-v3",
                "release_batch_size": batch_size,
                "release_batch_position": position,
                "owner_sample_after_started_ns": sample_started_ns,
                "owner_sample_after_finished_ns": sample_finished_ns,
                "owner_sample_ordered_after_batch": sample_ordered,
                "owner_identity_matches_after_batch": owner_identity_matches,
                "intent_token_matches_after_batch": token_matches,
                "owned_keycodes_after_batch": owned_after,
                "owner_transition_verified": batch_verified,
                "physical_verification_authoritative": False,
                "measurement_contract_v3": (
                    "all explicit key-up calls in this backend-held batch complete before "
                    "the one owner-state sample and before per-key telemetry publication"
                ),
            })
            if terminal_cleanup_verified is not None:
                receipt["release_batch_finalized_by_terminal_cleanup"] = True
                receipt["terminal_cleanup_verified"] = terminal_cleanup_verified
        for receipt in rows:
            self.emit(receipt)
        rows.clear()
