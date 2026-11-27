"""Independent integrity audit for the immutable R08 first outcome."""
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
    "old_fixture_exited_cleanly": d["recovery_fixture_exit_code"] == 0,
    "new_pid_and_generation": d["fresh_task_preflight"]["fixture_pid"] != d["fresh_task_preflight"]["previous_fixture_pid"] and d["fresh_task_preflight"]["native_identity"]["target_generation"] != d["recovery_phase"]["old_target_generation"],
    "old_generation_refused_before_input": stale["refusal_reason"] == "TARGET_GENERATION_CHANGED" and stale["input_dispatched"] is False,
    "compiled_task_action_once": len(d["compiled_task_receipt"]["standard_action_call_ids"]) == 1,
    "exact_fixture_effect": d["independent_effect"] == {"saved": True, "text": "office", "clicked": True},
    "exact_fixture_event_sequence": sum(row.get("kind") == "click" for row in d["task_fixture_events"]) == 1 and [row.get("code") for row in d["task_fixture_events"] if row.get("kind") == "char"] == list(map(ord, "office")) and sum(row.get("kind") == "save" for row in d["task_fixture_events"]) == 1,
    "post_observation_after_dispatch": d["task_phase_checks"]["post_dispatch_fresh_observation"] is True,
    "native_state_neutral": all(d["task_neutral_readback"][key] is False for key in ("SHIFT", "CTRL", "S", "left_button")),
    "independent_oracle_rejected_invalid_id": d["task_oracle"]["status"] == "unknown" and "oracle_id must be 32 lowercase hexadecimal characters" in d["task_oracle"]["task_effect"]["uncertainty"],
    "task_success_not_claimed": d["task_oracle"]["task_success"] is None,
    "cleanup_success": d["cleanup"]["fixture_exit_code"] == 0 and d["cleanup"]["foreground_before"] == d["cleanup"]["foreground_after_restore"],
    "failure_preserved": d["classification"] == "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED",
}
audit = {"attempt_id": d["attempt_id"], "experiment_pass": False,
    "checks": checks, "pretrial_hash_audit": pretrial, "raw_hash_audit": raw,
    "audit_pass": all(checks.values()) and not pretrial["errors"] and not raw["errors"]}
(PACKET / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(audit, indent=2, sort_keys=True))
if not audit["audit_pass"]:
    raise SystemExit(1)
