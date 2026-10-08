#!/usr/bin/env python3
"""Independent raw-only audit for the alias-refusal owner-cleanup construction."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    errors = []
    if sha(args.candidate) != freeze["candidate_sha256"]:
        errors.append("candidate_sha256_mismatch")
    for relative, expected in freeze["source_sha256"].items():
        actual = sha(args.freeze.parent / relative)
        if actual != expected:
            errors.append("source_sha256_mismatch:" + relative)
    if raw.get("status") != "CANDIDATE_COMPLETE" or raw.get("errors"):
        errors.append("candidate_incomplete_or_error")

    keys = raw.get("keycodes") or {}
    obs = raw.get("observations") or {}
    refusal = raw.get("refusal") or {}
    cleanup = raw.get("cleanup") or {}
    terminal = cleanup.get("terminal_release") or {}
    before_records = raw.get("owner_records_before_close") or []
    after_records = raw.get("owner_records_after_close") or []
    checks = {
        "a_and_A_resolve_to_same_nonzero_keycode": type(keys.get("a")) is int and keys.get("a") > 0 and keys.get("a") == keys.get("A"),
        "focused_key_down_admitted": (raw.get("admission") or {}).get("event") == "input_admission" and (obs.get("press_event") or {}).get("type") == 2 and (obs.get("press_event") or {}).get("keycode") == keys.get("a") and obs.get("server_down_before_alias") is True,
        "alias_batch_refused_as_duplicate_resolved_code": refusal.get("raised") is True and refusal.get("type") == "ValueError" and "distinct resolved keycodes" in str(refusal.get("message", "")),
        "refusal_preserved_held_key": obs.get("server_down_after_refusal") is True and obs.get("key_event_after_refusal") is None,
        "no_explicit_keyup_record_before_close": not any(isinstance(row, dict) and row.get("event") == "owner_explicit_keyup" for row in before_records),
        "close_delivered_matching_key_release": (obs.get("release_event_after_close") or {}).get("type") == 3 and (obs.get("release_event_after_close") or {}).get("keycode") == keys.get("a") and (obs.get("release_event_after_close") or {}).get("window") == raw.get("client_window"),
        "server_keymap_empty_after_close": obs.get("server_down_after_close") is False,
        "terminal_owner_release_verified_empty": terminal.get("event") == "owner_release" and terminal.get("verified") is True and terminal.get("keys_down") == [] and terminal.get("reason") == "close",
        "close_returned_and_owner_stopped": raw.get("close_returned") is True and cleanup.get("owner_closed") is True and cleanup.get("owner_stopped") is True and cleanup.get("owner_thread_alive") is False,
        "xvfb_exited_zero": cleanup.get("xvfb_exit") == 0,
        "exactly_one_terminal_release_record": sum(1 for row in after_records if isinstance(row, dict) and row.get("event") == "owner_release") == 1,
    }
    errors.extend(name for name, ok in checks.items() if not ok)
    decision = "PASS_METHOD_SCOPED" if not errors else ("STOP" if raw.get("status") != "CANDIDATE_COMPLETE" else "FAIL")
    result = {
        "schema": "release-batch-alias-owner-cleanup-a01-audit-v1",
        "candidate_sha256": sha(args.candidate),
        "raw_sha256": sha(args.raw),
        "checks": checks,
        "errors": errors,
        "decision": decision,
        "scope": "one guarded alias-refusal followed by actual V4/V3/V12 owner-close cleanup on isolated Xvfb; no game, task, physical keyboard, or live allocation",
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "errors": errors, "checks_passed": sum(checks.values()), "checks_total": len(checks)}, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
