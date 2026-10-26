"""Independent preregistration/raw hash and scoped recovery audit for R06."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def manifest(path, base):
    rows = path.read_text(encoding="utf-8").splitlines()
    errors = []
    for row in rows:
        expected, relative = row.split("  ", 1)
        target = base / relative
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual != expected:
            errors.append({"path": relative, "expected": expected, "actual": actual})
    return {"entries": len(rows), "errors": errors}


pretrial = manifest(PACKET / "PRETRIAL_SHA256SUMS", ROOT)
raw = manifest(RUN / "SHA256SUMS", RUN)
d = json.loads((RUN / "result.json").read_text(encoding="utf-8"))
cancel = d["retained_result"]["cancellation"]
custody = cancel["result"]
checks = {
    "frozen_attempt_id": d["attempt_id"] == "win32-native-sendinput-r06-20261026",
    "preflight_shift_up": d["preflight"]["shift_down"] is False,
    "fixture_process_identity_matches": d["preflight"]["state_query_witness"][0]["pid"] == d["fixture_pid"] and d["state_after_recovery"]["state_query_witness"][0]["pid"] == d["fixture_pid"],
    "public_generation_matches": d["public_observation_raw_report"]["target_generation"] == d["preflight"]["target_generation"],
    "real_shift_down_during_hold": d["state_during_hold"]["shift_down"] is True,
    "hold_generation_matches": d["state_during_hold"]["target_generation"] == d["preflight"]["target_generation"],
    "cancel_accepted_pending": d["cancel"]["status"] == "pending",
    "retained_recovery_confirmed": cancel["status"] == "recovered" and cancel["release_confirmed"] is True,
    "producer_retired": type(custody["producer_exit_code"]) is int and custody["producer_exit_code"] != 0,
    "recovery_under_deadline": 0 <= custody["cleanup_latency_ns"] < custody["cleanup_deadline_ns"] - custody["cleanup_requested_monotonic_ns"],
    "task_release_readback": d["state_after_recovery"]["shift_down"] is False and bool(d["state_after_recovery"]["state_query_witness"]),
    "readback_generation_matches": d["state_after_recovery"]["target_generation"] == d["preflight"]["target_generation"],
    "no_emergency_release": "emergency_release" not in d,
    "no_fixture_effect": d["effect_file_present"] is False and d["fixture_has_no_task_effect_events"] is True,
    "no_replay_or_task_claim": cancel["replay_allowed"] is False and cancel["task_success"] is None,
    "retained_call_identity_matches": d["retained_result"]["call_id"] == d["call_id"] and d["retained_result"]["action"]["operation_id"] == cancel["action_operation_id"],
    "fixture_exited": d["cleanup"]["fixture_exit_code"] == 0,
    "foreground_restored": d["cleanup"]["foreground_before"] == d["cleanup"]["foreground_after_restore"],
    "wslc_and_docker_unused": d["wslc_used"] is False and d["docker_used"] is False,
}
audit = {"attempt_id": d["attempt_id"], "classification": d["classification"],
    "pretrial_hash_audit": pretrial, "raw_hash_audit": raw,
    "checks": checks, "audit_pass": all(checks.values()) and
        not pretrial["errors"] and not raw["errors"] and
        d["classification"] == "PASS_SCOPED_BOUNDED_RECOVERY"}
(PACKET / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(audit, indent=2, sort_keys=True))
if not audit["audit_pass"]:
    raise SystemExit(1)
