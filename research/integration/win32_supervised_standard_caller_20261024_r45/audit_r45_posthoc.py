"""Additive audit of the R45 frozen first outcome; does not replay the attempt."""
import hashlib, json
from pathlib import Path
P=Path(__file__).resolve().parent
load=lambda n: json.loads((P/n).read_text(encoding="utf-8"))
C=load("conditions.json"); pre=load("preflight.json"); raw=load("raw.json")
a=load("audit_r36.json"); phases=load("phases.json"); gate=load("phase2_status.json")
checks=[]
def add(name,ok,evidence): checks.append({"name":name,"passed":bool(ok),"evidence":evidence})
rows=a["checks"]; failed=[r for r in rows if not r["passed"]]
hold=next((r for r in rows if r["name"]=="callback_held_for_full_1250ms_after_cancel_response"),{})
down=next((r for r in rows if r["name"]=="same_generation_q_down_before_cancel"),{})
up=next((r for r in rows if r["name"]=="same_generation_q_up_independently_observed_while_callback_held"),{})
cleanup=next((r for r in rows if r["name"]=="producer_retired_and_fixture_session_cleaned"),{})
source_ok=all(hashlib.sha256((P/rel).read_bytes()).hexdigest()==digest for rel,digest in C["frozen_files"].items())
add("frozen_packet_source_hashes_match",source_ok,{"source_count":len(C["frozen_files"])})
add("input_free_preflight_passed",pre.get("status")=="PASS" and pre.get("native_input_sent") is False,pre.get("checks"))
add("one_dispatch_and_one_cancel",raw.get("dispatch_attempts")==1 and raw.get("public_cancel_attempt",{}).get("attempt_count")==1,{"dispatch_attempts":raw.get("dispatch_attempts"),"cancel_attempt_count":raw.get("public_cancel_attempt",{}).get("attempt_count")})
add("same_generation_q_down_confirmed_before_cancel",bool(down.get("passed")),down.get("evidence"))
add("strict_release_gate_failed_only_on_frozen_hold_minimum",a.get("strict_release_gate_passed") is False and a.get("passed")==10 and a.get("total")==11 and len(failed)==1 and failed[0].get("name")=="callback_held_for_full_1250ms_after_cancel_response",{"passed":a.get("passed"),"total":a.get("total"),"failed_checks":[r.get("name") for r in failed],"callback_hold":hold.get("evidence")})
add("same_generation_q_up_observed_during_held_callback",bool(up.get("passed")),up.get("evidence"))
add("owned_producer_and_fixture_cleanup_passed",bool(cleanup.get("passed")),cleanup.get("evidence"))
no_phase2=(not (P/"task_raw.json").exists() and not (P/"run"/"phase2_task").exists() and "phase2_started_monotonic_ns" not in phases and gate.get("status")=="NOT_STARTED_PHASE1_GATE_FAILED")
add("phase2_not_started_after_gate_failure",no_phase2,{"phase2_status":gate,"phase2_started":phases.get("phase2_started_monotonic_ns")})
result={"schema":"win32-r45-posthoc-first-outcome-audit-v1","attempt_id":C["attempt_id"],"source_commit":C["source_commit"],"status":"FAIL_OR_UNKNOWN","checks_passed":sum(x["passed"] for x in checks),"checks_total":len(checks),"phase1_strict_status":a.get("status"),"phase1_gate_passed":False,"phase2_status":gate.get("status"),"task_success":None,"checks":checks}
(P/"audit_r45_posthoc.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"status":result["status"],"checks_passed":result["checks_passed"],"checks_total":result["checks_total"],"phase1":f"{a.get('passed')}/{a.get('total')}","phase2":gate.get("status")},sort_keys=True))
