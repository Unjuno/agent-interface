"""Join public task verification, its outer oracle receipt, and ammo evidence."""
from __future__ import annotations


def adjudicate_public_ammo_effect(public_result, oracle_receipt,
                                  ammo_transition, *, expected_call_id):
    """Return bounded exact-call checks without assuming receipt field nesting.

    The public normalized receipt deliberately contains outcome/identity but
    may omit the oracle's reason. The outer retained oracle receipt carries the
    reason; numeric before/after classification is independently checked.
    """
    checks = {}
    public_effect = (public_result.get("task_effect")
        if type(public_result) is dict else None)
    public_effect = public_effect if type(public_effect) is dict else {}
    normalized = public_effect.get("receipt")
    normalized = normalized if type(normalized) is dict else {}
    raw = oracle_receipt if type(oracle_receipt) is dict else {}
    raw_receipt = raw.get("receipt")
    raw_receipt = raw_receipt if type(raw_receipt) is dict else {}
    transition = ammo_transition if type(ammo_transition) is dict else {}
    before = transition.get("before")
    before = before if type(before) is dict else {}
    after = transition.get("after")
    after = after if type(after) is dict else {}

    checks["public_call_matches"] = (
        public_result.get("call_id") == expected_call_id
        if type(public_result) is dict else False)
    checks["public_task_success"] = public_result.get("task_success") is True \
        if type(public_result) is dict else False
    checks["public_effect_verified"] = (
        public_effect.get("status") == "verified"
        and normalized.get("outcome") == "success")
    checks["outer_oracle_reason"] = raw.get("reason") == "ammo_50_to_49"
    checks["receipt_call_matches"] = (
        normalized.get("call_id") == expected_call_id
        and raw_receipt.get("call_id") == expected_call_id)
    checks["receipt_operation_matches"] = bool(
        normalized.get("operation_id")
        and normalized.get("operation_id") == raw_receipt.get("operation_id"))
    checks["receipt_generation_matches"] = bool(
        normalized.get("target_generation")
        and normalized.get("target_generation")
        == raw_receipt.get("target_generation"))
    checks["numeric_transition_50_to_49"] = (
        transition.get("expected") == ["50", "49"]
        and before.get("status") == "classified"
        and before.get("value") == "50"
        and after.get("status") == "classified"
        and after.get("value") == "49")
    return {"status": "verified" if all(checks.values()) else "not_verified",
        "expected_call_id": expected_call_id,
        "operation_id": normalized.get("operation_id"),
        "target_generation": normalized.get("target_generation"),
        "checks": checks}
