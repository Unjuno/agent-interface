"""Versioned read-only audit repair for the A01 runner schema label."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def audit(raw: dict, manifest: dict) -> list[str]:
    errors = []
    for rel, expected in manifest["files"].items():
        path = ROOT / rel
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"source_hash:{rel}")
    if raw.get("candidate_exit") != 0 or raw.get("schema") != "batch-cancel-sync-composition-a01-raw-v1":
        errors.append("candidate_disposition")
    if raw.get("candidate_sha256") != manifest["files"]["candidate/input_owner_v12_composed.py"]:
        errors.append("candidate_hash_mismatch")
    if len(raw.get("cases", [])) != 2:
        errors.append("case_count")
    cases = {case.get("case"): case for case in raw.get("cases", [])}
    batch = cases.get("batch_cancel_during_sync", {})
    record = batch.get("receipt") or {}
    expected_codes = [ord("W") % 200 + 10, ord("A") % 200 + 10]
    expected_events = [[2, expected_codes[0]], [2, expected_codes[1]],
                       [3, expected_codes[0]], [3, expected_codes[1]]]
    intervals = record.get("key_release_intervals_ns", [])
    if record.get("event") != "owner_release" or record.get("reason") != "cancelled":
        errors.append("batch_cancel_cause")
    if record.get("verified") is not True or record.get("keys_down") != []:
        errors.append("batch_not_verified_empty")
    if batch.get("release_sync_delta") != 1:
        errors.append("batch_sync_count")
    if batch.get("key_events") != expected_events or batch.get("final_down") != []:
        errors.append("batch_key_event_order_or_state")
    if batch.get("cancel_set") is not True or len(intervals) != 2:
        errors.append("batch_cancel_or_interval_count")
    verified = record.get("verified_ns")
    for index, (item, expected_code) in enumerate(zip(intervals, expected_codes)):
        span = item.get("interval_ns") if isinstance(item, dict) else None
        if ((item.get("keycode") if isinstance(item, dict) else None) != expected_code or not isinstance(span, list)
                or len(span) != 2 or any(type(value) is not int for value in span)
                or span[0] > span[1] or type(verified) is not int or span[1] > verified):
            errors.append(f"batch_interval:{index}")
    explicit = cases.get("explicit_up_cancel_during_sync", {})
    receipt = explicit.get("receipt") or {}
    if (receipt.get("event") != "owner_explicit_keyup"
            or receipt.get("operation") != "up"
            or receipt.get("cancel_requested_after_sync") is not True
            or receipt.get("server_sync_completed") is not True
            or explicit.get("cancel_set") is not True):
        errors.append("explicit_up_cancellation_receipt")
    if explicit.get("key_events") != [[2, expected_codes[0]], [3, expected_codes[0]]]:
        errors.append("explicit_up_event_order")
    return errors


def main() -> None:
    manifest = json.loads((ROOT / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "raw/trace.json").read_text(encoding="utf-8"))
    errors = audit(raw, manifest)
    status = "PASS_SYNTHETIC_COMPOSITION" if not errors else "FAIL_AUDIT"
    print(json.dumps({"schema": "batch-cancel-sync-composition-a01-audit-v2",
                      "status": status, "case_count": 2, "errors": errors}, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
