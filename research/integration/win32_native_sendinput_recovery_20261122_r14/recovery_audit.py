"""Post-run independent partial-phase analysis; never grants full experiment acceptance."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=Path(__file__).resolve().parents[3]; RUN=P/"run"
def verify(path,resolver):
    rows=path.read_text(encoding="ascii").splitlines(); errors=[]; seen=set()
    for row in rows:
        expected,rel=row.split("  ",1); target=resolver(rel)
        if rel in seen or Path(rel).is_absolute() or ".." in Path(rel).parts: errors.append(rel); continue
        seen.add(rel); actual=hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if actual!=expected: errors.append(rel)
    return {"entries":len(rows),"errors":errors}
local={"conditions.json","PREREGISTRATION.md","runner.py","audit.py","custody_audit.py"}
pre=verify(P/"PRETRIAL_SHA256SUMS",lambda rel:(P/rel if rel in local else ROOT/rel))
raw=verify(RUN/"SHA256SUMS",lambda rel:RUN/rel)
c=json.loads((P/"conditions.json").read_text(encoding="utf-8")); d=json.loads((RUN/"result.json").read_text(encoding="utf-8"))
ret=d["retained_result"]; cancel=d["cancel"]; cxl=ret.get("cancellation") or {}; cr=cxl.get("result") or {}
h=d["post_recovery_late_input_horizon"]; events=d["fixture_events"]; checks={
 "pretrial_and_raw_manifests_valid":not pre["errors"] and not raw["errors"],
 "valid_frozen_condition_json":c["attempt_id"]==d["attempt_id"] and c["source_main"]==d["source_commit"],
 "exact_live_activation_and_neutral_preflight":d["phase1_computer_use_activation"].get("fixture_window_id")==d["target_hwnd"] and d["phase1_computer_use_activation"].get("activate_call_returned") is True and d["window_preflight"].get("foreground_hwnd")==d["target_hwnd"] and d["preflight"].get("shift_down") is False and bool(d["preflight"].get("state_query_witness")),
 "pre_expiry_cancel_refused":d["pre_expiry_cancel"]["body"].get("status")=="cancel_not_due" and d["pre_expiry_cancel"]["started_monotonic_ns"]<d["pre_expiry_cancel"]["deadline_monotonic_ns"],
 "post_expiry_public_cancel_started":d["cancel_started_monotonic_ns"]>=d["pre_expiry_cancel"]["deadline_monotonic_ns"] and cr.get("cleanup_requested_monotonic_ns",0)>=d["pre_expiry_cancel"]["deadline_monotonic_ns"] and ret.get("deadline_cancel_policy")=="public_caller" and ret.get("deadline_cancel_route")=="public_interface_cancel",
 "terminal_release_receipt_exact_and_bounded":cancel.get("status")=="pending" and cxl.get("status")=="recovered" and cxl.get("release_confirmed") is True and cr.get("release_confirmed") is True and cr.get("operation_id")==ret.get("action",{}).get("operation_id") and cr.get("target_generation")==d["preflight"]["target_generation"] and type(cr.get("cleanup_latency_ns")) is int and 0<=cr["cleanup_latency_ns"]<3_000_000_000,
 "producer_stopped_and_late_input_horizon_clean":d["blocked_producer_after_recovery"].get("alive") is False and h.get("duration_ns",0)>=1_900_000_000 and h.get("sample_count",0)>=20 and h.get("max_sample_gap_ns",10**18)<=100_000_000 and h.get("all_shift_up") is True and h.get("one_generation") is True and h.get("target_generation")==d["preflight"]["target_generation"],
 "no_phase1_effect":d.get("effect_file_present") is False and events==[{"hwnd":d["target_hwnd"],"kind":"ready"}],
 "fixture_cleanup_and_foreground_restore":d.get("cleanup",{}).get("fixture_exit_code")==0 and d["cleanup"].get("foreground_before")==d["cleanup"].get("foreground_after_restore"),
 "phase2_not_run_after_strict_phase1_gate":d.get("fresh_task_preflight") is None and "task_phase_checks" not in d and d.get("classification")=="FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED",
 "no_wslc_or_docker":d.get("wslc_used") is False and d.get("docker_used") is False}
observed_physical=all(checks[k] for k in ["pretrial_and_raw_manifests_valid","valid_frozen_condition_json","exact_live_activation_and_neutral_preflight","pre_expiry_cancel_refused","post_expiry_public_cancel_started","terminal_release_receipt_exact_and_bounded","producer_stopped_and_late_input_horizon_clean","no_phase1_effect","fixture_cleanup_and_foreground_restore","no_wslc_or_docker"])
report={"attempt_id":d["attempt_id"],"classification":"PHASE1_RECOVERY_OBSERVED_ASYNC_RESULT_PHASE2_NOT_RUN","checks":checks,"pretrial_hash_audit":pre,"raw_hash_audit":raw,"phase1_physical_recovery_observed":observed_physical,"strict_phase1_gate_pass":False,"strict_gate_failure":"first interface_cancel response was pending; the frozen acceptance gate requires recovered on that response","terminal_interface_results_recovery":"recovered; release_confirmed=true; cleanup_latency_ns=%s"%cr.get("cleanup_latency_ns"),"phase2_task_tested":False,"full_experiment_acceptance_pass":False,"note":"A subsequent public interface_results read returned the terminal verified recovery receipt, but this does not satisfy the frozen direct-cancel response predicate."}
(P/"recovery-audit.json").write_text(json.dumps(report,indent=2,sort_keys=True)+chr(10),encoding="utf-8")
print(json.dumps(report,indent=2,sort_keys=True))
if not all(checks.values()): raise SystemExit(1)