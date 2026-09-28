"""Separate reference implementation for the receipt contract audit."""
import random

from release_protocol_v2 import ProtocolError, validate_receipt, validate_stream


AUTO = {"lease_expired", "cancelled", "focus_invalid", "owner_close", "owner_stop"}
CALLER = ("caller_started_ns", "caller_returned_ns")
OWNER = ("owner_release_started_ns", "owner_sync_returned_ns")


def oracle(row):
    """Independent structural oracle; intentionally not a wrapper around candidate checks."""
    if row.get("schema") != "owner-keyup-release-v2" or row.get("grants_input_authority") is not False:
        return False
    if not all(isinstance(row.get(k), str) and row[k] for k in ("owner_id", "intent_token", "key")):
        return False
    if type(row.get("owner_sequence")) is not int or row["owner_sequence"] < 1:
        return False
    if row.get("owned_before") is not True or row.get("owned_after") is not False:
        return False
    if not all(type(row.get(k)) is int and row[k] >= 0 for k in OWNER):
        return False
    a, b = (row[k] for k in OWNER)
    if b < a:
        return False
    if row.get("release_kind") == "explicit_client_up":
        if row.get("operation") not in ("up", "button_up"):
            return False
        if not isinstance(row.get("request_id"), str) or not row["request_id"]:
            return False
        if not all(type(row.get(k)) is int and row[k] >= 0 for k in CALLER):
            return False
        c0, c1 = (row[k] for k in CALLER)
        return c0 <= a <= b <= c1 and row.get("release_reason") is None
    if row.get("release_kind") == "autonomous_cleanup":
        return (row.get("operation") is None and row.get("request_id") is None
                and row.get("release_reason") in AUTO and not any(k in row for k in CALLER))
    return False


def explicit(seed, seq, key):
    start = seed * 100
    return {
        "schema": "owner-keyup-release-v2", "release_kind": "explicit_client_up",
        "operation": "up", "request_id": f"r{seed}", "release_reason": None,
        "owner_id": "owner", "intent_token": f"i{seed}", "key": key,
        "owner_sequence": seq, "caller_started_ns": start,
        "owner_release_started_ns": start + 1, "owner_sync_returned_ns": start + 2,
        "caller_returned_ns": start + 3, "owned_before": True,
        "owned_after": False, "grants_input_authority": False,
    }


def autonomous(seed, seq, reason):
    start = seed * 100
    return {
        "schema": "owner-keyup-release-v2", "release_kind": "autonomous_cleanup",
        "operation": None, "request_id": None, "release_reason": reason,
        "owner_id": "owner", "intent_token": f"i{seed}", "key": "Down",
        "owner_sequence": seq, "owner_release_started_ns": start,
        "owner_sync_returned_ns": start + 1, "owned_before": True,
        "owned_after": False, "grants_input_authority": False,
    }


def main():
    checks = 0
    for seed in range(1, 501):
        row = explicit(seed, seed, "Down") if seed % 2 else autonomous(seed, seed, sorted(AUTO)[seed % len(AUTO)])
        expected = oracle(row)
        try:
            validate_receipt(row)
            actual = True
        except ProtocolError:
            actual = False
        if actual != expected or not expected:
            raise AssertionError(f"candidate/reference disagreement at generated case {seed}")
        checks += 1
        corrupt = dict(row)
        if row["release_kind"] == "explicit_client_up":
            corrupt["caller_returned_ns"] = corrupt["owner_sync_returned_ns"] - 1
        else:
            corrupt["caller_started_ns"] = corrupt["owner_release_started_ns"] - 1
        expected_bad = oracle(corrupt)
        try:
            validate_receipt(corrupt)
            actual_bad = True
        except ProtocolError:
            actual_bad = False
        if expected_bad or actual_bad:
            raise AssertionError(f"corruption accepted at generated case {seed}")
        checks += 1

    good = [explicit(7, 1, "Down"), explicit(7, 2, "space")]
    if oracle(good[0]) is not True or oracle(good[1]) is not True:
        raise AssertionError("multi-key positive oracle failed")
    stream = validate_stream(good)
    if stream["explicit_receipts"] != 2 or stream["authority_grants"] != 0:
        raise AssertionError("multi-key stream summary mismatch")
    checks += 1
    print({"status": "PASS_INDEPENDENT_REFERENCE_AUDIT", "generated_comparisons": checks,
           "valid_cases": 500, "corruptions_rejected": 500, "errors": []})


if __name__ == "__main__":
    main()
