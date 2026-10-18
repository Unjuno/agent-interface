from __future__ import annotations
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent

def audit(result):
    errors = []
    def check(ok, name):
        if not ok:
            errors.append(name)
    check(result.get("candidate_invocations") == 1, "one candidate invocation")
    check(result.get("candidate_source") == "PR #7429 head 8fe1160c89cba797dacc235e28441d1660c13845",
          "frozen source identity")
    success = result.get("success_arm", {})
    check(success.get("callback_entered") is True, "accepted callback entered")
    check(success.get("execute_before_baseline_release") is False, "worker gated by callback")
    check(success.get("baseline_before_execute") is True, "baseline precedes first backend step")
    check(success.get("baseline_and_submit_thread_match") is True, "baseline on submit caller thread")
    check(success.get("terminal_status") == "completed", "fake program completed")
    check(success.get("worker_stopped") is True, "success worker stopped")
    failure = result.get("failure_arm", {})
    check(failure.get("exception") == {"type": "RuntimeError", "message": "injected scorer baseline failure"},
          "injected baseline failure surfaced")
    check(failure.get("backend_execute_count") == 0, "failed baseline issued no input step")
    check(failure.get("worker_started") is False and failure.get("worker_alive") is False,
          "failed baseline left worker unstarted")
    check(failure.get("active_id_after_failure") == "barrier-failure", "failed baseline leaves active slot stuck")
    check(failure.get("used_id_retained") is True and failure.get("backend_lease_set") is True,
          "failed baseline leaves admission state committed")
    return errors

result = json.loads((ROOT / "RESULT.json").read_text())
errors = audit(result)
mutations = {}
for name, change in {
    "worker_before_baseline": lambda row: row["success_arm"].update(baseline_before_execute=False),
    "action_despite_failed_baseline": lambda row: row["failure_arm"].update(backend_execute_count=1),
    "failure_did_not_stick": lambda row: row["failure_arm"].update(active_id_after_failure=None),
}.items():
    altered = copy.deepcopy(result)
    change(altered)
    mutations[name] = bool(audit(altered))
if not all(mutations.values()):
    errors.append("negative control escaped")
summary = {
    "schema": "admission-baseline-barrier-a01-audit-v1",
    "scope": "frozen executor with deterministic fake backend and synthetic baseline callback",
    "errors": errors,
    "passed": not errors,
    "negative_controls_rejected": mutations,
    "classification": "BARRIER_CONFIRMED_FAILURE_PATH_STOP" if not errors else "STOP",
}
(ROOT / "AUDIT.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps(summary, sort_keys=True))
raise SystemExit(bool(errors))
