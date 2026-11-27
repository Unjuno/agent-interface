"""Audit the R39 paired recovery and fresh-generation task sequence."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
C = json.loads((P / "conditions.json").read_text(encoding="utf-8"))
checks = []


def check(name, passed, evidence):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})


preflight = json.loads((P / "preflight.json").read_text(encoding="utf-8"))
release = json.loads((P / "audit_r36.json").read_text(encoding="utf-8"))
raw = json.loads((P / "raw.json").read_text(encoding="utf-8"))
phases = json.loads((P / "phases.json").read_text(encoding="utf-8"))
task_path = P / "task_raw.json"
task = json.loads(task_path.read_text(encoding="utf-8")) if task_path.exists() else {}
task_run = P / "run" / "phase2_task"
oracle_path = task_run / "oracle-evidence.json"
oracle = json.loads(oracle_path.read_text(encoding="utf-8")) if oracle_path.exists() else {}

old_observation = raw.get("public_observation", {}).get("raw_report", {})
old_generation = old_observation.get("target_generation")
new_generation = task.get("target_generation")
phase_start = phases.get("phase2_started_monotonic_ns")
oracle_time = oracle.get("observed_monotonic_ns")
task_effect = task.get("steps", [])
verify_rows = [row for row in task_effect if row.get("name") == "task_oracle"]
verify = (verify_rows[-1].get("parsed") or {}) if verify_rows else {}
receipt = ((verify.get("task_effect") or {}).get("receipt") or {})
expected = C["phase2_task"]["expected_effect"]
effect_path = task_run / "effect.json"
actual_effect = json.loads(effect_path.read_text(encoding="utf-8")) if effect_path.exists() else None
cleanup = task.get("cleanup") or {}
phase_rows = task.get("steps", [])
close_rows = [row for row in phase_rows if row.get("name") == "server_close"]
close_response = ((close_rows[-1].get("parsed") or {}) if close_rows else {})
dispatch_rows = [row for row in phase_rows if row.get("name") == "dispatch"]
dispatch_report = (dispatch_rows[-1].get("parsed") or {}) if dispatch_rows else {}
task_action = dispatch_report.get("action")
if not isinstance(task_action, dict):
    task_action = dispatch_report.get("result")
if not isinstance(task_action, dict) or task_action.get("status") != "completed":
    for group in (row for row in phase_rows if row.get("name") == "read_only_results"):
        for poll in group.get("polls", []):
            parsed = poll.get("parsed") or {}
            action = parsed.get("action")
            if isinstance(action, dict) and action.get("status") == "completed":
                task_action = action
                break
release_receipts = (((task_action or {}).get("result") or {}).get("execution") or {}).get("releases", [])
neutral_release = bool(release_receipts) and all(
    row.get("verified") is True
    and row.get("keys_down") == [] and row.get("buttons_down") == []
    and row.get("keys_unknown") == [] and row.get("buttons_unknown") == []
    for row in release_receipts)
has_independent_state_witness = any(
    bool(row.get("state_query_witnesses")) for row in release_receipts)
old_retained = raw.get("retained_report") or {}
old_call_id = (raw.get("public_dispatch", {}).get("response") or {}).get("call_id")
old_operation_id = old_retained.get("operation_id")

check("preflight_passed_without_input", preflight.get("status") == "PASS"
      and preflight.get("native_input_sent") is False, preflight.get("checks"))
check("phase1_strict_release_gate_passed",
      release.get("strict_release_gate_passed") is True,
      {"status": release.get("status"), "passed": release.get("passed"),
       "total": release.get("total")})
check("phase2_started_only_after_phase1_gate",
      release.get("strict_release_gate_passed") is True
      and type(phases.get("phase2_started_monotonic_ns")) is int
      and phases["phase2_started_monotonic_ns"] >= phases.get("phase1_audit_returned_monotonic_ns", 0),
      {"phase1_audit_returned_monotonic_ns": phases.get("phase1_audit_returned_monotonic_ns"),
       "phase2_started_monotonic_ns": phase_start})
check("fresh_target_generation",
      isinstance(old_generation, str) and isinstance(new_generation, str)
      and len(old_generation) == 64 and len(new_generation) == 64
      and old_generation != new_generation,
      {"phase1_generation": old_generation, "phase2_generation": new_generation})
check("distinct_call_and_operation",
      isinstance(task.get("call_id"), str) and task.get("call_id") != old_call_id
      and isinstance(task.get("operation_id"), str)
      and task.get("operation_id") != old_operation_id,
      {"phase1_call_id": old_call_id,
       "phase2_call_id": task.get("call_id"),
       "phase1_operation_id": old_operation_id,
       "phase2_operation_id": task.get("operation_id")})
check("task_oracle_success_bound_to_new_action",
      task.get("status") == "PASS_SCOPED"
      and verify.get("status") == "verified" and verify.get("task_success") is True
      and receipt.get("call_id") == task.get("call_id")
      and receipt.get("operation_id") == task.get("operation_id")
      and receipt.get("target_generation") == new_generation
      and receipt.get("oracle_id") == C["phase2_task"]["oracle_id"],
      {"status": verify.get("status"), "task_success": verify.get("task_success"),
       "receipt": receipt})
check("phase2_action_completed_with_verified_neutral_release",
      isinstance(task_action, dict) and task_action.get("status") == "completed"
      and task_action.get("operation_id") == task.get("operation_id")
      and task_action.get("target_generation") == new_generation
      and task_action.get("release_confirmed") is True
      and ((task_action.get("result") or {}).get("recovery_required") is False)
      and neutral_release,
      {"action_status": (task_action or {}).get("status"),
       "release_confirmed": (task_action or {}).get("release_confirmed"),
       "recovery_required": ((task_action or {}).get("result") or {}).get("recovery_required"),
       "release_receipts": release_receipts})
check("phase2_completion_readback_has_independent_state_witness",
      has_independent_state_witness,
      {"release_receipt_count": len(release_receipts),
       "state_query_witnesses_present": has_independent_state_witness})
check("task_effect_exactly_matches_frozen_expectation",
      actual_effect == expected and oracle.get("outcome") == "success"
      and oracle.get("actual") == expected,
      {"expected": expected, "actual": actual_effect,
       "oracle_outcome": oracle.get("outcome"),
       "oracle_actual": oracle.get("actual")})
check("task_effect_observed_after_recovery_phase",
      type(phase_start) is int and type(oracle_time) is int
      and oracle_time >= phase_start,
      {"phase2_started_monotonic_ns": phase_start,
       "oracle_observed_monotonic_ns": oracle_time})
check("phase2_cua_activation_receipt_matches_fresh_fixture",
      (task.get("foreground_activation") or {}).get("activated") is True
      and (task.get("foreground_activation") or {}).get("screenshot_inspected") is True
      and bool((task.get("foreground_activation") or {}).get("activation_result"))
      and (task.get("foreground_activation") or {}).get("fixture_hwnd") == task.get("fixture_hwnd")
      and (task.get("foreground_activation") or {}).get("observed_foreground_hwnd") == task.get("fixture_hwnd")
      and bool((task.get("foreground_activation") or {}).get("cua_window_id")),
      {"foreground_activation": task.get("foreground_activation"),
       "fixture_hwnd": task.get("fixture_hwnd")})
check("bounded_cleanup_and_foreground_restore",
      phases.get("phase2_exit_code") == 0 and cleanup.get("fixture_exit_code") == 0
      and cleanup.get("foreground_restored") is True
      and close_response.get("status") == "closed",
      {"phase2_exit_code": phases.get("phase2_exit_code"),
       "fixture_exit_code": cleanup.get("fixture_exit_code"),
       "foreground_restored": cleanup.get("foreground_restored"),
       "server_close": close_response})

passed = sum(row["passed"] for row in checks)
status = "PASS_SCOPED" if passed == len(checks) else "FAIL_OR_UNKNOWN"
result = {"schema": "win32-r42-combined-audit-v1",
    "attempt_id": C["attempt_id"], "source_commit": C["source_commit"],
    "status": status, "passed": passed, "total": len(checks),
    "phase1_release_status": release.get("status"),
    "task_success": verify.get("task_success"),
    "checks": checks,
    "nonclaims": C["nonclaims"],
    "conditions_sha256": hashlib.sha256((P / "conditions.json").read_bytes()).hexdigest()}
(P / "audit_r37.json").write_text(json.dumps(result, indent=2,
    sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"status": status, "passed": passed,
    "total": len(checks), "task_success": verify.get("task_success")}, sort_keys=True))
