"""Caller/owner-thread joined key-up receipts for the v39 telemetry path."""

from input_owner_v11 import InputOwner as OwnerWithKeyUpReceipt
from input_transition_owner_v3 import InputOwner as Previous


class InputOwner(Previous):
    """Join exactly one owner-thread KeyRelease/XSync record to each explicit up."""

    def __init__(self, display_name, _owner_cls=OwnerWithKeyUpReceipt):
        super().__init__(display_name, _owner_cls=_owner_cls)

    def call(self, operation, lease=None, key=None):
        if operation != "up":
            return super().call(operation, lease, key)

        records_before = self.records
        transition = super().call(operation, lease, key)
        records_after = self.records
        history_complete = (
            len(records_after) >= len(records_before)
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
            and receipt.get("physical_verification_authoritative") is False
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
            "ordinary_release_candidate": (
                transition.get("ordinary_release_candidate") is True and receipt_valid
            ),
            "release_measurement_contract_v4": (
                "one identity-bound owner-thread XTest KeyRelease/XSync receipt is nested "
                "inside the caller's explicit-up bracket; XSync does not prove application use"
            ),
        })
        return result
