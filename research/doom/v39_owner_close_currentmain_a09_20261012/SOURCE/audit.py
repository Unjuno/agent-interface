"""Independent raw-only audit of the current-main V39 owner-close Xvfb case."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_TOKEN = "v39-owner-close-a09"
EXPECTED_KEY = "a"
EXPECTED_DISPLAY = ":131"
SOURCE_NAMES = (
    "input_owner_v10.py",
    "input_owner_v12.py",
    "input_transition_owner_v3.py",
    "input_transition_owner_v4.py",
)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def evaluate(raw, freeze, source_dir, candidate_path):
    errors = []
    if sha(candidate_path) != freeze.get("candidate_sha256"):
        errors.append("candidate_sha256_mismatch")
    for name in SOURCE_NAMES:
        expected = freeze.get("source_sha256", {}).get(name)
        actual_path = Path(source_dir) / name
        if not expected or not actual_path.is_file() or sha(actual_path) != expected:
            errors.append("source_sha256_mismatch:" + name)

    admission = raw.get("admission") if isinstance(raw.get("admission"), dict) else {}
    events = raw.get("client_events") if isinstance(raw.get("client_events"), list) else []
    cleanup = raw.get("cleanup") if isinstance(raw.get("cleanup"), dict) else {}
    records = raw.get("owner_records") if isinstance(raw.get("owner_records"), list) else []
    terminal = cleanup.get("terminal_release") if isinstance(cleanup.get("terminal_release"), dict) else {}
    keycode = raw.get("keycode")
    attempts_map = terminal.get("key_release_attempts")
    key_attempt = attempts_map.get(str(keycode)) if isinstance(attempts_map, dict) else None
    attempts = key_attempt.get("attempts") if isinstance(key_attempt, dict) else None
    attempt = attempts[0] if isinstance(attempts, list) and len(attempts) == 1 and isinstance(attempts[0], dict) else {}

    checks = {
        "candidate_complete": raw.get("status") == "CANDIDATE_COMPLETE" and raw.get("errors") == [],
        "one_accepted_key_admission": admission.get("event") == "input_admission" and admission.get("key") == EXPECTED_KEY and type(admission.get("keycode")) is int and admission.get("keycode") == keycode and type(admission.get("input_ack_ns")) is int and type(admission.get("admitted_ns")) is int and admission["admitted_ns"] <= admission["input_ack_ns"] and type(admission.get("valid_until_ns")) is int,
        "expected_display": raw.get("display") == EXPECTED_DISPLAY,
        "one_matching_press_release_pair": len(events) == 2 and [row.get("type") for row in events] == [2, 3] and all(row.get("keycode") == keycode and row.get("window") == raw.get("client_window") and type(row.get("observed_ns")) is int for row in events) and events[0]["observed_ns"] < events[1]["observed_ns"],
        "observer_keymap_up": raw.get("observer_key_up") is True,
        "one_owner_close_record": len(records) == 1 and records[0] == terminal and terminal.get("event") == "owner_release" and terminal.get("reason") == "close",
        "verified_empty_close_receipt": terminal.get("verified") is True and terminal.get("keys_down") == [] and terminal.get("buttons_down") == [] and terminal.get("keys_unknown") == [] and terminal.get("key_state_errors") == [] and terminal.get("intent_token") == EXPECTED_TOKEN,
        "per_key_release_attempt_verified": isinstance(key_attempt, dict) and key_attempt.get("verified") is True and len(attempts or []) == 1 and attempt.get("server_key_down_before") is True and attempt.get("server_key_down_after") is False and attempt.get("keyrelease_error") is None and attempt.get("sync_error") is None and type(attempt.get("keyrelease_started_ns")) is int and type(attempt.get("sync_returned_ns")) is int and type(attempt.get("keymap_sampled_ns")) is int and attempt["keyrelease_started_ns"] <= attempt["sync_returned_ns"] <= attempt["keymap_sampled_ns"],
        "owner_closed_and_stopped": cleanup.get("owner_closed") is True and cleanup.get("owner_stopped") is True and cleanup.get("owner_thread_alive") is False,
        "xvfb_exit_zero": cleanup.get("xvfb_exit") == 0,
    }
    errors.extend(name for name, passed in checks.items() if not passed)
    return {"checks": checks, "errors": errors, "decision": "PASS_METHOD_SCOPED" if not errors else ("STOP" if raw.get("status") != "CANDIDATE_COMPLETE" else "FAIL")}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--freeze", type=Path, required=True)
    ap.add_argument("--source-dir", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    raw_bytes = args.raw.read_bytes()
    raw = json.loads(raw_bytes)
    result = evaluate(raw, freeze, args.source_dir, args.candidate)
    result.update({
        "schema": "v39-owner-close-currentmain-xvfb-audit-a09-v1",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "candidate_sha256": sha(args.candidate),
        "base_main": freeze.get("base_main"),
        "scope": "one isolated synthetic Xvfb owner-close path; no physical keyboard, desktop/game, or task outcome",
    })
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "errors": result["errors"]}, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
