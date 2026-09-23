"""Typed DOOM adapter for race-hardened release telemetry v4.

V4 keeps the non-staggering v3 release path and strengthens only the single
post-batch attribution decision.  No extra X11/owner query is inserted between
individual releases.
"""
import threading

from doom_typed_coast_backend_v1 import Backend as Previous, suite
from input_transition_owner_v3 import InputOwner


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        self.owner.close()
        self.owner = InputOwner(session.name)
        self._release_batch = threading.local()

    def execute(self, step, cancel, identifier, index):
        previous = getattr(self._release_batch, "context", None)
        self._release_batch.context = {
            "rows": [], "identifier": identifier, "step": index
        }
        try:
            return super().execute(step, cancel, identifier, index)
        finally:
            if previous is None:
                try:
                    del self._release_batch.context
                except AttributeError:
                    pass
            else:
                self._release_batch.context = previous

    @staticmethod
    def _post_batch_authority(lease, after):
        if not isinstance(after, dict):
            return {
                "interruption_clear": False,
                "post_cancel_clear": False,
                "post_lease_time_valid": False,
                "active_deadline_matches": False,
                "local_focus_invalid_clear": False,
                "sampled_focus_matches": False,
                "post_batch_authority_verified": False,
            }

        snapshot = getattr(lease, "interruption_snapshot", None)
        interruption_clear = callable(snapshot) and snapshot() is None
        post_cancel_clear = after.get("cancel_requested") is False
        post_lease_time_valid = after.get("active_lease_time_valid") is True
        active_deadline_matches = (
            type(getattr(lease, "deadline", None)) is int
            and after.get("active_lease_deadline_ns") == lease.deadline
        )
        local_focus_invalid_clear = getattr(lease, "focus_invalid", False) is False
        expected_focus = getattr(lease, "expected_focus", None)
        sampled_focus_matches = (
            expected_focus is not None and after.get("focus") == expected_focus
        )
        verified = all((
            interruption_clear,
            post_cancel_clear,
            post_lease_time_valid,
            active_deadline_matches,
            local_focus_invalid_clear,
            sampled_focus_matches,
        ))
        return {
            "interruption_clear": interruption_clear,
            "post_cancel_clear": post_cancel_clear,
            "post_lease_time_valid": post_lease_time_valid,
            "active_deadline_matches": active_deadline_matches,
            "local_focus_invalid_clear": local_focus_invalid_clear,
            "sampled_focus_matches": sampled_focus_matches,
            "post_batch_authority_verified": verified,
        }

    def raw(self, key, down):
        if down:
            record = self.owner.call("down", self.lease, key)
            self.held.add(key)
            if record is not None:
                self.emit(record)
            return None

        context = getattr(self._release_batch, "context", None)
        if context is None:
            self.owner.call("up", self.lease, key)
            self.held.discard(key)
            return None

        was_backend_owned = key in self.held
        row = self.owner.call("up", self.lease, key)
        self.held.discard(key)
        if not isinstance(row, dict) or row.get("event") != "input_release_transition":
            raise AssertionError("v4 requires input-release-transition receipt")
        row = dict(row)
        row["backend_owned_before_release"] = was_backend_owned
        context["rows"].append(row)

        # Preserve v3's proven non-staggering invariant.
        if self.held:
            return None

        rows = context["rows"]
        after = self.owner.call("input_state")
        current_token = getattr(self.lease, "intent_token", None)
        latest_return_ns = max(row["release_call_returned_ns"] for row in rows)
        sample_started_ns = after.get("sample_started_ns") if isinstance(after, dict) else None
        sample_finished_ns = after.get("sample_finished_ns") if isinstance(after, dict) else None
        sample_ordered = (
            type(sample_started_ns) is int
            and type(sample_finished_ns) is int
            and latest_return_ns <= sample_started_ns <= sample_finished_ns
        )
        owner_id = after.get("owner_id") if isinstance(after, dict) else None
        owner_identity_matches = all(row.get("owner_id") == owner_id for row in rows)
        token_matches = all(row.get("intent_token") == current_token for row in rows)
        owned_after = after.get("owned_keycodes") if isinstance(after, dict) else None
        owner_empty = owned_after == []
        backend_ownership = all(
            row.get("backend_owned_before_release") is True for row in rows
        )
        request_time_ordinary = all(
            row.get("ordinary_release_candidate") is True for row in rows
        )
        authority = self._post_batch_authority(self.lease, after)
        batch_verified = bool(
            rows
            and sample_ordered
            and owner_identity_matches
            and token_matches
            and owner_empty
            and backend_ownership
            and request_time_ordinary
            and authority["post_batch_authority_verified"]
        )

        batch_size = len(rows)
        for position, receipt in enumerate(rows):
            receipt.update({
                "release_batch_schema": "input-release-batch-v4",
                "release_batch_size": batch_size,
                "release_batch_position": position,
                "release_batch_identifier": context["identifier"],
                "release_batch_step": context["step"],
                "owner_sample_after_started_ns": sample_started_ns,
                "owner_sample_after_finished_ns": sample_finished_ns,
                "owner_sample_ordered_after_batch": sample_ordered,
                "owner_identity_matches_after_batch": owner_identity_matches,
                "intent_token_matches_after_batch": token_matches,
                "owned_keycodes_after_batch": owned_after,
                **authority,
                "owner_transition_verified": batch_verified,
                "physical_verification_authoritative": False,
                "grants_input_authority": False,
                "measurement_contract_v4": (
                    "v3 back-to-back release ordering plus fail-closed post-batch "
                    "authority revalidation using the existing single owner sample "
                    "and the lease interruption record"
                ),
            })
        for receipt in rows:
            self.emit(receipt)
        rows.clear()
        return None
