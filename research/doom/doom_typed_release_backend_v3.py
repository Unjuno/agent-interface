"""Typed DOOM backend composing v2 attribution with owner-thread release batches."""
from __future__ import annotations

import threading

from doom_typed_release_backend_v2 import Backend as Previous, suite
from input_transition_owner_v4 import InputOwner


class Backend(Previous):
    """Opt-in release composition; controller and default backend are unchanged."""

    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        self.owner.close()
        self.owner = InputOwner(session.name)
        self._release_batch = threading.local()
        self.release_batch_publication_reports = []

    def execute(self, step, cancel, identifier, index):
        previous = getattr(self._release_batch, "context", None)
        if previous is not None and previous.get("identifier") == identifier:
            context = previous
        else:
            context = {"rows": [], "identifier": identifier}
        context["step"] = index
        self._release_batch.context = context
        try:
            result = super().execute(step, cancel, identifier, index)
        except BaseException as exc:
            disposition = (
                "publication_exception"
                if context.get("publication_error_type") is not None
                else "step_exception"
            )
            self._finish_incomplete_release_batch(context, exc, disposition)
            raise

        if context["rows"]:
            self._release_batch.context = context
        else:
            try:
                del self._release_batch.context
            except AttributeError:
                pass
        return result

    def _publish_incomplete_release_batch(self, context, error, *, disposition):
        """Keep observed per-key up receipts when later cleanup cannot finish."""
        rows = context["rows"]
        size = len(rows)
        for position, row in enumerate(rows):
            row.setdefault("release_batch_size", size)
            row.setdefault("release_batch_position", position)
            row.update({
                "release_batch_schema": "input-release-batch-v3",
                "release_batch_complete": False,
                "release_batch_disposition": disposition,
                "release_batch_error_type": type(error).__name__,
                "owner_sample_after_batch_available": False,
                "owner_transition_verified": False,
                "owner_thread_keyup_verified_after_batch": False,
                "physical_verification_authoritative": False,
                "measurement_contract_v3": (
                    "release telemetry is incomplete or publication failed; "
                    "release_batch_disposition identifies the exception boundary"
                ),
            })
            self.emit(row)

    def _finish_incomplete_release_batch(self, context, error, disposition):
        report = context.get("release_batch_publication_report")
        if isinstance(report, dict):
            for item in report["rows"]:
                if item["status"] == "pending":
                    item["status"] = "not_attempted"
        try:
            self._publish_incomplete_release_batch(
                context, error, disposition=disposition
            )
        except BaseException as publish_exc:
            add_note = getattr(error, "add_note", None)
            if callable(add_note):
                add_note(
                    "incomplete release telemetry publication failed: "
                    + type(publish_exc).__name__
                )
        finally:
            context["rows"].clear()
            try:
                del self._release_batch.context
            except AttributeError:
                pass

    def release_all(self):
        context = getattr(self._release_batch, "context", None)
        try:
            result = super().release_all()
        except BaseException as exc:
            if context is not None:
                if context["rows"]:
                    self._finish_incomplete_release_batch(
                        context, exc, "release_all_exception"
                    )
                else:
                    try:
                        del self._release_batch.context
                    except AttributeError:
                        pass
            raise
        if context is not None and context["rows"]:
            self._publish_release_batch(
                context,
                terminal_cleanup_verified=(
                    isinstance(result, dict) and result.get("verified") is True
                ),
            )
            try:
                del self._release_batch.context
            except AttributeError:
                pass
        return result

    def raw(self, key, down):
        input_context = self._input_event_context
        if input_context is None:
            raise RuntimeError("keyboard input outside program/step telemetry context")

        if down:
            record = self.owner.call("down", self.lease, key)
            self.held.add(key)
            if record is not None:
                row = dict(record)
                row["id"], row["step"] = input_context
                row.setdefault("owner_id", self.owner.owner_id)
                row.setdefault("intent_token", getattr(self.lease, "intent_token", None))
                self.emit(row)
            return None

        context = getattr(self._release_batch, "context", None)
        if context is None:
            self.owner.call("up", self.lease, key)
            self.held.discard(key)
            return None

        was_backend_owned = key in self.held
        records = getattr(self.owner, "records", None)
        record_count = len(records) if isinstance(records, list) else None
        row = self.owner.call("up", self.lease, key)
        self.held.discard(key)
        if not isinstance(row, dict) or row.get("event") != "input_release_transition":
            raise AssertionError("v4 release wrapper did not return transition receipt")
        row = dict(row)
        row["backend_owned_before_release"] = was_backend_owned
        row["release_batch_identifier"] = context["identifier"]
        row["release_batch_step"] = context["step"]
        row["id"], row["step"] = input_context
        row["owner_cleanup_record_count_before_release"] = record_count
        context["rows"].append(row)
        if not self.held:
            self._publish_release_batch(context)
        return None

    def _publish_release_batch(self, context, *, terminal_cleanup_verified=None):
        rows = context["rows"]
        records = getattr(self.owner, "records", None)
        counts = [row.get("owner_cleanup_record_count_before_release") for row in rows]
        counts_valid = (
            isinstance(records, list)
            and all(type(count) is int and 0 <= count <= len(records) for count in counts)
        )
        first_count = min(counts) if counts_valid else None
        records_since_first_release = records[first_count:] if counts_valid else None
        after = self.owner.call("input_state")
        token = getattr(self.lease, "intent_token", None)
        latest_return = max(row["release_call_returned_ns"] for row in rows)
        sample_started = after.get("sample_started_ns") if isinstance(after, dict) else None
        sample_finished = after.get("sample_finished_ns") if isinstance(after, dict) else None
        sample_ordered = (
            type(sample_started) is int and type(sample_finished) is int
            and latest_return <= sample_started <= sample_finished
        )
        owner_matches = all(row.get("owner_id") == after.get("owner_id") for row in rows)
        token_matches = all(row.get("intent_token") == token for row in rows)
        owner_empty = after.get("owned_keycodes") == []
        owned_before = all(row.get("backend_owned_before_release") is True for row in rows)
        ordinary = all(row.get("ordinary_release_candidate") is True for row in rows)
        cleanup_records = []
        explicit_receipts = [row.get("owner_thread_keyup_receipt") for row in rows]
        explicit_records = (
            [record for record in records_since_first_release
             if isinstance(record, dict) and record.get("event") == "owner_explicit_keyup"]
            if isinstance(records_since_first_release, list) else None
        )
        records_valid = (
            isinstance(records_since_first_release, list)
            and counts_valid
            and all(isinstance(record, dict) for record in records_since_first_release)
        )
        if records_valid:
            for record in records_since_first_release:
                if record.get("event") == "owner_explicit_keyup":
                    continue
                if record.get("event") != "owner_release":
                    records_valid = False
                    break
                if not (
                    type(record.get("verified_ns")) is int
                    and record.get("verified") is True
                    and record.get("keys_down") == []
                    and record.get("buttons_down") == []
                    and isinstance(record.get("reason"), str)
                ):
                    records_valid = False
                    break
                cleanup_records.append(record)
        if explicit_records != explicit_receipts:
            records_valid = False
        brackets_valid = all(
            type(row.get("release_call_started_ns")) is int
            and type(row.get("release_call_returned_ns")) is int
            and row["release_call_started_ns"] <= row["release_call_returned_ns"]
            for row in rows
        )
        no_cleanup_overlap = records_valid and all(
            not (
                row["release_call_started_ns"] <= record["verified_ns"]
                <= row["release_call_returned_ns"]
            )
            for row in rows for record in cleanup_records
        )
        owner_keyup = all(row.get("owner_thread_keyup_verified") is True for row in rows)
        cleanup_ok = terminal_cleanup_verified is not False
        if terminal_cleanup_verified is True:
            cleanup_ok = cleanup_ok and records_valid and any(
                record.get("reason") in ("release", "cancelled", "stop_requested", "thread_exit")
                and record.get("verified") is True
                for record in cleanup_records
            )
        verified = bool(
            rows and cleanup_ok and sample_ordered and owner_matches and token_matches
            and owner_empty and owned_before and ordinary and records_valid
            and brackets_valid and no_cleanup_overlap and owner_keyup
        )
        size = len(rows)
        report = {
            "id": context["identifier"],
            "step": context["step"],
            "release_batch_size": size,
            "rows": [
                {"position": position, "key": row.get("key"), "status": "pending"}
                for position, row in enumerate(rows)
            ],
        }
        context["release_batch_publication_report"] = report
        self.release_batch_publication_reports.append(report)
        for position, row in enumerate(rows):
            row.update({
                "release_batch_schema": "input-release-batch-v3",
                "release_batch_size": size,
                "release_batch_position": position,
                "release_batch_complete": True,
                "owner_sample_after_started_ns": sample_started,
                "owner_sample_after_finished_ns": sample_finished,
                "owner_sample_ordered_after_batch": sample_ordered,
                "owner_identity_matches_after_batch": owner_matches,
                "intent_token_matches_after_batch": token_matches,
                "owned_keycodes_after_batch": after.get("owned_keycodes"),
                "owner_transition_verified": verified,
                "owner_thread_keyup_verified_after_batch": owner_keyup,
                "physical_verification_authoritative": False,
                "measurement_contract_v3": (
                    "all explicit key-up calls in this backend-held batch complete before "
                    "the one owner-state sample and before per-key telemetry publication"
                ),
            })
            if terminal_cleanup_verified is not None:
                row["release_batch_finalized_by_terminal_cleanup"] = True
                row["terminal_cleanup_verified"] = terminal_cleanup_verified
        while rows:
            # Mark delivery attempt before crossing the sink boundary. If a
            # sink accepts a row and then raises, execute() must not retry it.
            row = rows.pop(0)
            status = report["rows"][row["release_batch_position"]]
            status["status"] = "delivery_unknown"
            try:
                self.emit(row)
            except BaseException as exc:
                context["publication_error_type"] = type(exc).__name__
                report["publication_error_type"] = type(exc).__name__
                raise
            else:
                status["status"] = "confirmed"
