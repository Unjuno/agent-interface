"""Caller/owner-thread joined key-up receipts for the v39 telemetry path."""

from input_owner_v12 import InputOwner as OwnerWithKeyUpReceipt
from input_transition_owner_v3 import InputOwner as Previous


class InputOwner(Previous):
    """Join exactly one owner-thread KeyRelease/XSync record to each explicit up."""

    def __init__(self, display_name, _owner_cls=OwnerWithKeyUpReceipt):
        super().__init__(display_name, _owner_cls=_owner_cls)

    def call(self, operation, lease=None, key=None):
        if operation != "up":
            return super().call(operation, lease, key)

        owner_records = getattr(getattr(self, "_inner", None), "records", None)
        records_before = list(owner_records) if isinstance(owner_records, list) else None
        transition = super().call(operation, lease, key)
        records_after = getattr(getattr(self, "_inner", None), "records", None)
        history_complete = (
            isinstance(records_before, list)
            and isinstance(records_after, list)
            and len(records_after) >= len(records_before)
            and records_after[:len(records_before)] == records_before
        )
        new_records = records_after[len(records_before):] if history_complete else []
        owner_rows = [
            row for row in new_records
            if isinstance(row, dict)
            and row.get("event") == "owner_explicit_keyup"
            and row.get("operation") == "up"
            and row.get("key") == key
        ]
        receipt = owner_rows[0] if len(owner_rows) == 1 else None

        caller_started = transition.get("release_call_started_ns") if isinstance(transition, dict) else None
        caller_returned = transition.get("release_call_returned_ns") if isinstance(transition, dict) else None
        owner_started = receipt.get("owner_keyrelease_started_ns") if receipt else None
        owner_returned = receipt.get("owner_sync_returned_ns") if receipt else None
        keymap_sampled = receipt.get("owner_keymap_sampled_ns") if receipt else None
        keyup_attempt_count = receipt.get("server_keyup_attempt_count") if receipt else None
        keyup_attempts = receipt.get("server_keyup_attempts") if receipt else None
        attempts_valid = (
            type(keyup_attempts) is list
            and type(keyup_attempt_count) is int
            and len(keyup_attempts) == keyup_attempt_count
            and 1 <= keyup_attempt_count <= 3
            and type(keyup_attempts[0]) is dict
            and type(keyup_attempts[-1]) is dict
            and keyup_attempts[0].get("keyrelease_started_ns") == receipt.get(
                "owner_keyrelease_started_ns")
            and keyup_attempts[-1].get("sync_returned_ns") == receipt.get(
                "owner_sync_returned_ns")
            and keyup_attempts[-1].get("keymap_sampled_ns") == receipt.get(
                "owner_keymap_sampled_ns")
            and all(
                type(attempt) is dict
                and attempt.get("attempt") == index
                and type(attempt.get("keyrelease_started_ns")) is int
                and type(attempt.get("sync_returned_ns")) is int
                and type(attempt.get("keymap_sampled_ns")) is int
                and attempt["keyrelease_started_ns"] <= attempt["sync_returned_ns"]
                <= attempt["keymap_sampled_ns"]
                and type(attempt.get("server_key_down_before")) is bool
                and type(attempt.get("server_key_down_after")) is bool
                for index, attempt in enumerate(keyup_attempts, 1)
            )
            and all(
                previous["keymap_sampled_ns"] <= current["keyrelease_started_ns"]
                and previous["server_key_down_after"] is current["server_key_down_before"]
                for previous, current in zip(keyup_attempts, keyup_attempts[1:])
            )
            and keyup_attempts[-1].get("server_key_down_after") is False
        )
        cancel_after_sync = receipt.get("cancel_requested_after_sync") if receipt else None
        token = self._intent_token(lease)
        receipt_valid = bool(
            history_complete
            and isinstance(transition, dict)
            and len(owner_rows) == 1
            and isinstance(receipt, dict)
            and receipt.get("owner_id") == self.owner_id
            and receipt.get("intent_token") == token
            and isinstance(token, str) and token
            and receipt.get("valid_until_ns") == transition.get("valid_until_ns")
            and receipt.get("server_sync_completed") is True
            and receipt.get("server_keyup_verified") is True
            and receipt.get("server_key_down_after_keyup") is False
            and receipt.get("key_state_source") == "x11_query_keymap"
            and attempts_valid
            and type(keymap_sampled) is int and owner_returned <= keymap_sampled
            and receipt.get("physical_verification_authoritative") is False
            and type(cancel_after_sync) is bool
            and type(caller_started) is int
            and type(owner_started) is int
            and type(owner_returned) is int
            and type(caller_returned) is int
            and caller_started <= owner_started <= owner_returned <= caller_returned
        )
        if not isinstance(transition, dict):
            return transition

        result = dict(transition)
        result.update({
            "owner_thread_keyup_receipt": dict(receipt) if receipt is not None else None,
            "owner_thread_keyup_receipt_count": len(owner_rows) if history_complete else 0,
            "owner_thread_keyup_history_complete": history_complete,
            "owner_thread_keyup_verified": receipt_valid,
            "cancel_requested_after_sync": cancel_after_sync,
            "ordinary_release_candidate": (
                transition.get("ordinary_release_candidate") is True
                and receipt_valid and cancel_after_sync is False
            ),
            "release_measurement_contract_v4": (
                "one identity-bound owner-thread XTest KeyRelease/XSync receipt is nested "
                "inside the caller's explicit-up bracket; bounded X11 keymap samples verify "
                "server key state only and do not prove physical keyboard state or application use"
            ),
        })
        return result
