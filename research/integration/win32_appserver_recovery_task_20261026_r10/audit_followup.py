"""Additive correction: R10 preregistration entries are packet-relative."""
import hashlib
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def verify(path, base):
    failures = []
    rows = path.read_text(encoding="utf-8").splitlines()
    for row in rows:
        expected, relative = row.split("  ", 1)
        target = base / relative
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual != expected:
            failures.append({"path": relative, "expected": expected, "actual": actual})
    return {"entries": len(rows), "failures": failures}


pretrial = verify(PACKET / "PRETRIAL_SHA256SUMS", PACKET)
raw = verify(RUN / "SHA256SUMS", RUN)
d = json.loads((RUN / "result.json").read_text(encoding="utf-8"))
requests = [json.loads(path.read_text(encoding="utf-8"))
    for path in (RUN / "task-server").glob("*/request.json")]
dispatch_programs = [row.get("arguments", {}).get("program", {}).get("program_id")
    for row in requests if row.get("tool") == "interface_dispatch"]
checks = {
    "first_outcome_retained_as_failure": d.get("attempt_id") == "win32-appserver-recovery-r10-20261026" and d.get("classification") == "FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED",
    "bounded_phase_one_recovery_passed": (d.get("recovery_phase") or {}).get("classification") == "PASS_SCOPED_BOUNDED_RECOVERY" and (d.get("recovery_phase") or {}).get("release_confirmed") is True and 0 <= (d.get("recovery_phase") or {}).get("cleanup_latency_ns", -1) < 3_000_000_000 and (d.get("recovery_phase") or {}).get("same_generation_readback_up") is True,
    "old_generation_refused_before_any_input": (d.get("stale_generation_probe") or {}).get("refusal_reason") == "TARGET_GENERATION_CHANGED" and (d.get("stale_generation_probe") or {}).get("input_dispatched") is False,
    "runner_stopped_at_python_runtime_gate": d.get("error_type") == "AppServerUnsupportedRuntime" and "Python 3.12 or later" in d.get("error", "") and d.get("model_decision") is None,
    "no_task_action_or_effect": not any(value == "r10-appserver-grounded-click-save" for value in dispatch_programs) and d.get("independent_effect") is None and d.get("task_action_call_id") is None,
    "cleanup_and_host_restoration": (d.get("cleanup") or {}).get("fixture_exit_code") == 0 and (d.get("cleanup") or {}).get("foreground_before") == (d.get("cleanup") or {}).get("foreground_after_restore"),
    "no_wslc_or_docker": d.get("wslc_used") is False and d.get("docker_used") is False,
}
result = {"attempt_id": d.get("attempt_id"),
    "classification": "FAIL_RUNTIME_PREREQUISITE_RETAINED",
    "frozen_audit_hash_base_correction": "PRETRIAL_SHA256SUMS paths are packet-relative; the frozen audit mistakenly resolved them from the repository root. Original audit.json is preserved.",
    "pretrial_hash_audit": pretrial, "raw_hash_audit": raw,
    "task_server_dispatch_program_ids": dispatch_programs,
    "checks": checks, "audit_pass": all(checks.values()) and
        not pretrial["failures"] and not raw["failures"]}
(PACKET / "audit_followup.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
    encoding="utf-8", newline="\n")
print(json.dumps(result, indent=2, sort_keys=True))
if not result["audit_pass"]:
    raise SystemExit(1)
