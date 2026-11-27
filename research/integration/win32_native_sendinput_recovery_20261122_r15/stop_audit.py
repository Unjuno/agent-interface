"""Audit the R15 dispatch stop and preserve the pre-existing durable fence."""
import hashlib,json,os
from pathlib import Path
P=Path(__file__).resolve().parent; R=P/"run"; ROOT=Path(__file__).resolve().parents[3]
local={"conditions.json","PREREGISTRATION.md","runner.py","audit.py","custody_audit.py"}
def verify(path,resolver):
 rows=path.read_text(encoding="ascii").splitlines(); errors=[]
 for row in rows:
  sha,rel=row.split("  ",1); f=resolver(rel); actual=hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else None
  if actual!=sha: errors.append(rel)
 return {"entries":len(rows),"errors":errors}
pre=verify(P/"PRETRIAL_SHA256SUMS",lambda rel:(P/rel if rel in local else ROOT/rel)); raw=verify(R/"SHA256SUMS",lambda rel:R/rel)
d=json.loads((R/"result.json").read_text(encoding="utf-8")); c=json.loads((P/"conditions.json").read_text(encoding="utf-8"))
dispatch_pair=None
for reqpath in R.glob("server/*/request.json"):
 reqrow=json.loads(reqpath.read_text(encoding="utf-8"))
 if reqrow.get("operation")=="dispatch": dispatch_pair=(reqrow,reqpath.parent/"report.json"); break
if dispatch_pair is None: raise SystemExit("dispatch request/report not retained")
req,report_path=dispatch_pair; report=json.loads(report_path.read_text(encoding="utf-8"))
raw_events=[json.loads(x) for x in (R/"fixture/events.jsonl").read_text(encoding="utf-8").splitlines()]
fence=json.loads((P/"durable-fence-state.json").read_text(encoding="utf-8")); pending=fence.get("pending") or {}
r14=json.loads((ROOT/"research/integration/win32_native_sendinput_recovery_20261122_r14/run/result.json").read_text(encoding="utf-8"))
r14action=(r14.get("retained_result",{}).get("action") or {}); r14pid=(r14.get("blocked_producer_after_recovery") or {}).get("pid")
checks={
 "frozen_pretrial_and_raw_hashes":not pre["errors"] and not raw["errors"],
 "exact_source_and_attempt":c["attempt_id"]==d.get("attempt_id")=="win32-native-sendinput-r15-20261122" and c["source_main"]==d.get("source_commit")=="fd24ed40e452e16865b9725af4f3d97b0067d9d6",
 "phase1_activation_and_neutral_native_preflight":d.get("phase1_computer_use_activation",{}).get("fixture_window_id")==d.get("target_hwnd") and d.get("window_preflight",{}).get("foreground_hwnd")==d.get("target_hwnd") and d.get("preflight",{}).get("shift_down") is False and bool(d.get("preflight",{}).get("state_query_witness")),
 "public_observation_without_input":d.get("public_observation_raw_report",{}).get("input_dispatched") is False,
 "dispatch_refused_by_preexisting_durable_fence":report.get("status")=="invalid_request" and report.get("error")=="ORPHAN_RECOVERY_UNRESOLVED" and report.get("operation_invoked") is False and report.get("input_dispatched") is False and req.get("operation")=="dispatch",
 "source_fence_matches_R14_unknown_action":fence.get("status")=="unresolved" and pending.get("phase")=="unknown" and pending.get("gate_state")=="authorized" and pending.get("operation_id")==r14action.get("operation_id") and pending.get("target_generation")==r14.get("preflight",{}).get("target_generation") and pending.get("obligations")==r14action.get("obligations") and pending.get("late_input_horizon_required") is True,
 "no_new_input_or_task_effect":raw_events==[{"hwnd":d.get("target_hwnd"),"kind":"ready"}] and not (R/"fixture/effect.json").exists() and d.get("public_observation_raw_report",{}).get("input_dispatched") is False,
 "fixture_cleanup_and_foreground_restore":d.get("cleanup",{}).get("fixture_exit_code")==0 and d["cleanup"].get("foreground_before")==d["cleanup"].get("foreground_after_restore"),
 "no_retry_or_admitted_dispatch":len(list(R.rglob("result.json")))==1 and req.get("session",{}).get("call_count")==0,
 "original_producer_reported_stopped":(r14.get("blocked_producer_after_recovery") or {}).get("alive") is False and (r14.get("blocked_producer_after_recovery") or {}).get("exit_code") is not None and r14pid==pending.get("producer_identity",{}).get("pid")}
result={"attempt_id":d.get("attempt_id"),"disposition":"STOPPED_BY_DURABLE_CUSTODY_FENCE","checks":checks,"pretrial_hash_audit":pre,"raw_hash_audit":raw,"durable_fence_sha256":hashlib.sha256((P/"durable-fence-state.json").read_bytes()).hexdigest(),"custody_and_exclusion_audit_pass":all(checks.values()),"experiment_acceptance_pass":False,"note":"No R15 input was admitted. The repository-preserved R14 source action remains UNKNOWN in the protected per-logon fence; only the documented one-shot orphan-recovery route may resolve it."}
(P/"stop-audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+chr(10),encoding="utf-8")
print(json.dumps(result,indent=2,sort_keys=True))
if not all(checks.values()): raise SystemExit(1)