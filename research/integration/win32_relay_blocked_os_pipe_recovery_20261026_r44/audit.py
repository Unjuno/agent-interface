"""Verify R43's preregistered source and immutable raw manifest."""
import hashlib
import json
import argparse
from pathlib import Path

PACKET = Path(__file__).resolve().parent
ROOT = PACKET.parents[2]
RUN = PACKET / "run"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(path, base):
    failures = []
    seen = set()
    rows = path.read_text(encoding="utf-8-sig").splitlines()
    for line in rows:
        if not line.strip():
            continue
        digest, relative = line.split("  ", 1)
        if relative in seen:
            failures.append(f"duplicate:{relative}")
            continue
        seen.add(relative)
        candidate = (base / relative).resolve()
        if not candidate.is_relative_to(base.resolve()) or not candidate.is_file():
            failures.append(f"missing_or_escape:{relative}")
        elif sha(candidate) != digest:
            failures.append(f"hash_mismatch:{relative}")
    return {"entries": len(seen), "failures": failures}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretrial-only", action="store_true")
    args = parser.parse_args()
    pretrial = verify_manifest(PACKET / "PRETRIAL_SHA256SUMS", ROOT)
    if args.pretrial_only:
        print(json.dumps({"pretrial": pretrial}, indent=2))
        return 1 if pretrial["failures"] else 0
    result_path = RUN / "result.json"
    raw = verify_manifest(RUN / "SHA256SUMS", RUN) if (RUN / "SHA256SUMS").is_file() else {
        "entries": 0, "failures": ["raw_manifest_missing"]}
    result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {}
    failures = list(pretrial["failures"]) + list(raw["failures"])
    if result.get("attempt_id") != "win32-public-relay-os-pipe-r44-20261026":
        failures.append("attempt_id_mismatch")
    classification = result.get("classification")
    if classification == "PASS_OS_PIPE_BLOCKED_RELAY_RECOVERY":
        receipt = result.get("retained_result", {}).get("cancellation", {})
        cleanup = result.get("cleanup", {})
        if result.get("os_pipe_blocked_release_gate") is not True:
            failures.append("blocked_pipe_release_gate_missing")
        if receipt.get("status") != "recovered" or receipt.get("release_confirmed") is not True:
            failures.append("retained_recovery_receipt_invalid")
        if result.get("final_state", {}).get("shift_down") is not False:
            failures.append("final_same_generation_shift_up_missing")
        if cleanup.get("fixture_exit_code") != 0:
            failures.append("fixture_exit_not_zero")
        if cleanup.get("foreground_before_restore") != cleanup.get("foreground_after_restore"):
            failures.append("foreground_restore_mismatch")
    elif classification == "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED":
        if result.get("call_id") and not result.get("cancel_sent") and not result.get("failure_path_cancel_sent"):
            failures.append("post_dispatch_failure_without_cancel_attempt")
        if result.get("call_id") and not result.get("failure_path_exact_results") and not result.get("retained_result"):
            failures.append("post_dispatch_failure_without_exact_result_attempt")
    else:
        failures.append("unrecognized_classification")
    print(json.dumps({"classification": classification,
        "pretrial": pretrial, "raw": raw, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
