"""Conservative identity join for retained V39 DOWN and release rows."""
from __future__ import annotations
from collections import Counter
from typing import Any

IDENTITY = ("id", "step", "intent_token", "owner_id", "key")


def _identity(row: dict[str, Any]) -> tuple[Any, ...] | None:
    values = tuple(row.get(k) for k in IDENTITY)
    return values if all(type(v) is str and v for v in values[:1] + values[2:]) and type(values[1]) is int else None


def join(raw: dict[str, Any]) -> dict[str, Any]:
    events = raw.get("events")
    if type(events) is not list:
        return {"status": "HOLD_INVALID_EVENT_CONTAINER", "pairs": []}
    downs = [e for e in events if type(e) is dict and e.get("event") == "input_admission"]
    ups = [e for e in events if type(e) is dict and e.get("event") == "input_release_transition"]
    down_ids = [_identity(e) for e in downs]
    up_ids = [_identity(e) for e in ups]
    if any(i is None for i in down_ids + up_ids):
        return {"status": "HOLD_MISSING_IDENTITY", "pairs": []}
    dc, uc = Counter(down_ids), Counter(up_ids)
    if any(n != 1 for n in dc.values()) or any(n != 1 for n in uc.values()):
        return {"status": "HOLD_AMBIGUOUS_IDENTITY", "pairs": []}
    if dc != uc:
        return {"status": "HOLD_UNMATCHED_ADMISSION_OR_RELEASE", "pairs": []}
    by_id = {i: row for i, row in zip(down_ids, downs)}
    up_by_id = {i: row for i, row in zip(up_ids, ups)}
    pairs = []
    for ident in sorted(dc, key=lambda x: (x[1], x[4])):
        down, up = by_id[ident], up_by_id[ident]
        receipt = up.get("owner_thread_keyup_receipt")
        if type(receipt) is not dict:
            return {"status": "HOLD_MISSING_OWNER_RECEIPT", "pairs": []}
        if any(receipt.get(k) != up.get(k) for k in ("intent_token", "owner_id", "key")):
            return {"status": "HOLD_RECEIPT_IDENTITY_MISMATCH", "pairs": []}
        if receipt.get("operation") != "up" or receipt.get("server_sync_completed") is not True:
            return {"status": "HOLD_UNVERIFIED_OWNER_RECEIPT", "pairs": []}
        if up.get("owner_thread_keyup_verified") is not True or up.get("physical_verification_authoritative") is not False:
            return {"status": "HOLD_RECEIPT_SCOPE_OR_VERIFICATION", "pairs": []}
        admitted = down.get("admitted_ns")
        release_start, release_end = up.get("release_call_started_ns"), up.get("release_call_returned_ns")
        keyup_start, sync_end = receipt.get("owner_keyrelease_started_ns"), receipt.get("owner_sync_returned_ns")
        times = (admitted, release_start, keyup_start, sync_end, release_end)
        if any(type(t) is not int for t in times) or not (admitted <= release_start <= keyup_start <= sync_end <= release_end):
            return {"status": "FAIL_INVALID_OR_REVERSED_TIME_ORDER", "pairs": []}
        pairs.append({
            "identity": dict(zip(IDENTITY, ident)),
            "admitted_ns": admitted,
            "release_call_started_ns": release_start,
            "owner_keyrelease_started_ns": keyup_start,
            "owner_sync_returned_ns": sync_end,
            "release_call_returned_ns": release_end,
            "physical_verification_authoritative": False,
        })
    operations = raw.get("operations")
    if type(operations) is not list:
        return {"status": "HOLD_MISSING_OPERATION_TRACE", "pairs": []}
    up_indices = [i for i, op in enumerate(operations) if type(op) is dict and op.get("op") == "key-up"]
    if len(up_indices) != len(ups):
        return {"status": "HOLD_OPERATION_RELEASE_COUNT_MISMATCH", "pairs": []}
    expected_codes = [row["owner_thread_keyup_receipt"].get("keycode") for row in sorted(ups, key=lambda row: row.get("release_call_started_ns", -1))]
    actual_codes = [operations[i].get("keycode") for i in up_indices]
    if actual_codes != expected_codes:
        return {"status": "FAIL_RELEASE_OPERATION_ORDER_MISMATCH", "pairs": []}
    between = operations[up_indices[0] + 1:up_indices[1]] if len(up_indices) >= 2 else []
    if between != raw.get("between_up_operations"):
        return {"status": "FAIL_INTER_UP_TRACE_MISMATCH", "pairs": []}
    if any(type(op) is dict and op.get("op") == "query_keymap" for op in between):
        return {"status": "FAIL_INTER_UP_KEYMAP_QUERY", "pairs": []}
    if raw.get("keymap_queries_between_ups") != 0:
        return {"status": "FAIL_INTER_UP_QUERY_COUNT", "pairs": []}
    effect_rows = raw.get("independent_task_effects")
    # The startup closure raw has no such field. Never synthesize effects from XSync.
    if type(effect_rows) is not list or not effect_rows:
        status = "PASS_IDENTITY_JOIN_SCOPED; HOLD_MISSING_TASK_EFFECT"
    else:
        status = "HOLD_EFFECT_LINKAGE_NOT_IMPLEMENTED"
    return {"status": status, "pairs": pairs, "independent_task_effect_count": len(effect_rows) if type(effect_rows) is list else 0}
