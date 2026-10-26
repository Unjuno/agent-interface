"""Independent evidence-integrity and first-outcome audit for R07."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def verify(path, base):
    rows = path.read_text(encoding="utf-8").splitlines()
    errors = []
    for row in rows:
        expected, relative = row.split("  ", 1)
        target = base / relative
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual != expected:
            errors.append({"path": relative, "expected": expected, "actual": actual})
    return {"entries": len(rows), "errors": errors}


pretrial = verify(PACKET / "PRETRIAL_SHA256SUMS", ROOT)
raw = verify(RUN / "SHA256SUMS", RUN)
d = json.loads((RUN / "result.json").read_text(encoding="utf-8"))
stale = d["stale_generation_probe"]
checks = {
    "recovery_phase_passed": d["recovery_phase"]["classification"] == "PASS_SCOPED_BOUNDED_RECOVERY",
    "old_fixture_exited_before_task_phase": d["recovery_fixture_exit_code"] == 0,
    "fresh_pid_differs": d["fresh_task_preflight"]["fixture_pid"] != d["fresh_task_preflight"]["previous_fixture_pid"],
    "fresh_generation_differs": d["fresh_task_preflight"]["native_identity"]["target_generation"] != d["recovery_phase"]["old_target_generation"],
    "stale_probe_sent_no_input": stale["input_dispatched"] is False,
    "stale_probe_failed_for_schema_reason": stale["refusal_reason"] == "release_all must appear exactly once",
    "no_continuation_effect": stale["effect_file_present"] is False and not (RUN / "task-fixture" / "effect.json").exists(),
    "task_session_action_count_zero": d["close"]["session"]["call_count"] == 0,
    "task_fixture_only_ready_event": all(json.loads(row).get("kind") == "ready" for row in (RUN / "task-fixture" / "events.jsonl").read_text(encoding="utf-8").splitlines()),
    "fixture_cleanup_failure_retained": d["cleanup"]["fixture_exit_code"] == 1,
    "overall_failure_retained": d["classification"] == "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED",
}
audit = {"attempt_id": d["attempt_id"], "experiment_pass": False,
    "first_outcome_preserved": True, "checks": checks,
    "pretrial_hash_audit": pretrial, "raw_hash_audit": raw,
    "audit_pass": all(checks.values()) and not pretrial["errors"] and not raw["errors"]}
(PACKET / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(audit, indent=2, sort_keys=True))
if not audit["audit_pass"]:
    raise SystemExit(1)
