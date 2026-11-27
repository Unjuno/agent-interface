from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
C=json.loads((P/"conditions.json").read_text(encoding="utf-8"))
R=json.loads((P/"raw.json").read_text(encoding="utf-8"))
checks=[]
def add(name,ok,evidence=None): checks.append({"name":name,"passed":bool(ok),"evidence":evidence or {}})
first=R.get("retained_report") or {}
sup=first.get("supervision") or {}
action=sup.get("action") or {}
cancel=sup.get("cancellation") or {}
action_result=action.get("result") or {}
cr=cancel.get("result") or {}
hook=R.get("hook_stopped") or {}
events=hook.get("events") or []
qd=next((e for e in events if e.get("message")==256 and e.get("vk")==81),{})
qu=next((e for e in events if e.get("message")==257 and e.get("vk")==81),{})
producer=R.get("producer_exit_witness") or {}
read=R.get("independent_readback") or {}
fixture=R.get("fixture") or {}
gen=(fixture.get("target_identity") or {}).get("generation")
add("frozen_source_and_preflight",R.get("source_commit")==C["source_commit"] and R.get("source_tracked_tree_clean") is True and json.loads((P/"preflight.json").read_text())["status"]=="PASS",{"source":R.get("source_commit"),"expected":C["source_commit"],"tracked_clean":R.get("source_tracked_tree_clean")})
add("single_cancelled_dispatch",R.get("dispatch_attempts")==1 and R.get("public_cancel",{}).get("response",{}).get("status")=="pending",{"dispatch_attempts":R.get("dispatch_attempts"),"cancel_return":R.get("public_cancel",{}).get("response",{}).get("status")})
add("callback_forward_and_exact_producer_exit",qd.get("callback_return_ns",0)>qd.get("callback_entry_ns",0) and qu.get("callback_entry_ns",0)>qd.get("callback_return_ns",0) and producer.get("status")=="exited" and producer.get("pid")==((cr.get("producer_identity") or {}).get("pid")) and producer.get("creation_time_100ns")==((cr.get("producer_identity") or {}).get("creation_time_100ns")) and producer.get("observed_monotonic_ns",0)>=qd.get("callback_return_ns",0),{"q_down":qd,"q_up":qu,"producer_exit":producer})
add("recovery_confirmed_in_action_and_cancel",cancel.get("status")=="recovered" and cancel.get("release_confirmed") is True and action.get("status")=="recovered" and action_result.get("status")=="recovered" and action_result.get("release_confirmed") is True and action.get("target_generation")==gen==cancel.get("target_generation"),{"cancel_status":cancel.get("status"),"action_status":action.get("status"),"cancel_release":cancel.get("release_confirmed"),"action_result":action_result})
add("independent_same_generation_q_up",read.get("status")=="observed" and read.get("q_down") is False and read.get("generation_before")==gen==read.get("generation_after") and read.get("returned_monotonic_ns",0)>qd.get("callback_return_ns",0),{"readback":read})
add("pre_cancel_fixture_effect",R.get("effect_readback")==C["trial"]["pre_recovery_effect"],{"actual":R.get("effect_readback"),"expected":C["trial"]["pre_recovery_effect"]})
post_obs=(R.get("post_recovery_observation") or {}).get("raw_report") or {}
add("fresh_observe_same_generation",post_obs.get("status")=="returned" and post_obs.get("target_generation_consistency")=="matched" and post_obs.get("target_generation")==gen,{"target_generation":gen,"post_observation":post_obs})
second=((R.get("post_recovery_dispatch") or {}).get("response") or {})
add("same_generation_fresh_action_refused_before_input",second.get("status")=="invalid_request" and second.get("error")=="fresh target generation required after cancellation" and second.get("operation_invoked") is False and second.get("input_dispatched") is False and R.get("post_recovery_call_id") is None,{"response":second,"accepted_call_id":R.get("post_recovery_call_id"),"attempts":R.get("post_recovery_dispatch_attempts")})
add("no_post_recovery_effect_or_task_success_claim",R.get("post_recovery_effect_readback") is None and ((R.get("retained_report") or {}).get("task_success")) is None and action_result.get("task_success") is None,{"post_effect":R.get("post_recovery_effect_readback"),"task_success":(R.get("retained_report") or {}).get("task_success")})
add("owned_cleanup_and_no_emergency_input",fixture.get("exit_code")==0 and fixture.get("window_exists_after_exit") is False and hook.get("thread_exited") is True and (R.get("foreground_restore") or {}).get("restored") is True and R.get("emergency_q_up") is None and (R.get("session_close_report") or {}).get("status")=="closed",{"fixture_exit":fixture.get("exit_code"),"window_exists_after_exit":fixture.get("window_exists_after_exit"),"hook_exited":hook.get("thread_exited"),"foreground_restore":R.get("foreground_restore"),"emergency_q_up":R.get("emergency_q_up"),"close":R.get("session_close_report")})
all_ok=all(c["passed"] for c in checks)
status="HYPOTHESIS_REJECTED_FAIL_CLOSED" if all_ok else "FAIL_OR_UNKNOWN"
out={"schema":"win32-supervised-standard-caller-r23-followup-audit-v1","attempt_id":C["attempt_id"],"status":status,"passed":sum(c["passed"] for c in checks),"total":len(checks),"hypothesis_accepted":False,"raw_sha256":hashlib.sha256((P/"raw.json").read_bytes()).hexdigest(),"checks":checks,"interpretation":"Recovery and independent same-generation release passed. A separately observed and newly leased action was rejected because it used the same target generation as the recovered operation. The refusal occurred before invocation and input (operation_invoked=false, input_dispatched=false); no action call ID was accepted and no post-recovery fixture effect occurred. This confirms a fail-closed same-generation reuse gate, not post-recovery task continuation. The frozen R23 continuation hypothesis is rejected. A new-generation/new-session path remains a separate untested attempt."}
(P/"audit_followup.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"status":status,"passed":out["passed"],"total":out["total"],"failed":[c["name"] for c in checks if not c["passed"]]},sort_keys=True))
