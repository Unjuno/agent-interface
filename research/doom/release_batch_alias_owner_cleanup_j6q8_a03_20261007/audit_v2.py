#!/usr/bin/env python3
"""Read-only structural successor audit for the saved A03 raw; never runs candidate."""
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
    parser.add_argument("--audit-freeze", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    base = json.loads(args.freeze.read_text(encoding="utf-8"))
    audit_freeze = json.loads(args.audit_freeze.read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    errors = []
    if sha(args.raw) != audit_freeze["raw_sha256"]:
        errors.append("raw_sha256_mismatch")
    if sha(args.candidate) != base["candidate_sha256"]:
        errors.append("candidate_sha256_mismatch")
    if sha(Path(__file__)) != audit_freeze["auditor_sha256"]:
        errors.append("auditor_sha256_mismatch")
    if sha(args.freeze) != audit_freeze["base_freeze_sha256"]:
        errors.append("base_freeze_sha256_mismatch")
    for relative, expected in base["source_sha256"].items():
        if sha(args.freeze.parent / relative) != expected:
            errors.append("source_sha256_mismatch:" + relative)
    if raw.get("status") != "CANDIDATE_COMPLETE" or raw.get("errors"):
        errors.append("candidate_incomplete_or_error")

    keys = raw.get("keycodes") or {}
    obs = raw.get("observations") or {}
    press = obs.get("press_event") or {}
    release = obs.get("release_event_after_close") or {}
    refusal = raw.get("refusal") or {}
    cleanup = raw.get("cleanup") or {}
    terminal = cleanup.get("terminal_release") or {}
    before = raw.get("owner_records_before_close") or []
    after = raw.get("owner_records_after_close") or []
    checks = {
        "a_A_alias_same_nonzero_code": type(keys.get("a")) is int and keys.get("a") > 0 and keys.get("a") == keys.get("A"),
        "key_down_admitted_and_observed": (raw.get("admission") or {}).get("event") == "input_admission" and press.get("type") == 2 and press.get("keycode") == keys.get("a") and obs.get("server_down_before_alias") is True,
        "resolved_alias_batch_refused": refusal.get("raised") is True and refusal.get("type") == "ValueError" and "distinct resolved keycodes" in str(refusal.get("message", "")),
        "refusal_did_not_emit_or_release": obs.get("server_down_after_refusal") is True and obs.get("key_event_after_refusal") is None and not any(isinstance(row, dict) and row.get("event") == "owner_explicit_keyup" for row in before),
        "close_release_matches_press_window_and_key": release.get("type") == 3 and release.get("keycode") == keys.get("a") and release.get("window") == press.get("window") and type(press.get("window")) is int,
        "close_release_observed_after_verified_receipt": type(terminal.get("verified_ns")) is int and type(release.get("observed_ns")) is int and terminal["verified_ns"] <= release["observed_ns"],
        "keymap_neutral_after_close": obs.get("server_down_after_close") is False,
        "terminal_release_is_verified_empty_close": terminal.get("event") == "owner_release" and terminal.get("verified") is True and terminal.get("keys_down") == [] and terminal.get("keys_unknown") == [] and terminal.get("reason") == "close",
        "owner_closed_and_thread_stopped": raw.get("close_returned") is True and cleanup.get("owner_closed") is True and cleanup.get("owner_stopped") is True and cleanup.get("owner_thread_alive") is False,
        "exactly_one_owner_terminal_release": sum(1 for row in after if isinstance(row, dict) and row.get("event") == "owner_release") == 1,
        "xvfb_exited_zero": cleanup.get("xvfb_exit") == 0,
    }
    errors.extend(name for name, passed in checks.items() if not passed)
    decision = "PASS_METHOD_SCOPED_AUDIT_V2" if not errors else ("STOP" if raw.get("status") != "CANDIDATE_COMPLETE" else "FAIL")
    result = {
        "schema": "release-batch-alias-owner-cleanup-a03-audit-v2",
        "decision": decision,
        "auditor_sha256": sha(Path(__file__)),
        "raw_sha256": sha(args.raw),
        "candidate_sha256": sha(args.candidate),
        "predecessor_audit_v1": {
            "decision": "FAIL",
            "reason": "its release-event check required a client_window raw field that candidate omitted; v2 binds release to the actually recorded press-event window",
        },
        "checks": checks,
        "errors": errors,
        "scope": "read-only audit of one already completed guarded alias-refusal and actual V4/V3/V12 owner-close Xvfb trace; no candidate rerun, game, task, physical keyboard, or live allocation",
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "errors": errors, "checks_passed": sum(checks.values()), "checks_total": len(checks)}, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
