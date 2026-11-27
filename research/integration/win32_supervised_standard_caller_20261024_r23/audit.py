from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
C=json.loads((HERE/"conditions.json").read_text(encoding="utf-8"))
R=json.loads((HERE/"raw.json").read_text(encoding="utf-8"))
checks=[]
def add(name,ok,evidence=None): checks.append({"name":name,"passed":bool(ok),"evidence":evidence or {}})
trial=C["trial"]
first=R.get("retained_report") or {}
first_super=first.get("supervision") or {}
first_action=first_super.get("action") or {}
first_cancel=first_super.get("cancellation") or {}
gen=(R.get("fixture") or {}).get("target_identity",{}).get("generation")
hook=R.get("hook_stopped") or {}
events=hook.get("events") or []
qd=next((e for e in events if e.get("message")==256 and e.get("vk")==81),{})
qu=next((e for e in events if e.get("message")==257 and e.get("vk")==81),{})
read=R.get("independent_readback") or {}
producer=R.get("producer_exit_witness") or {}
add("frozen_source_and_one_cancelled_dispatch",R.get("source_commit")==C["source_commit"] and R.get("source_tracked_tree_clean") is True and R.get("dispatch_attempts")==1 and first_cancel.get("status")=="recovered",{"source_commit":R.get("source_commit"),"tracked_clean":R.get("source_tracked_tree_clean"),"dispatch_attempts":R.get("dispatch_attempts"),"cancellation":first_cancel.get("status")})
add("producer_retired_and_hook_forwarded",producer.get("status")=="exited" and producer.get("pid")==((first_cancel.get("result") or {}).get("producer_identity") or {}).get("pid") and qd.get("callback_return_ns",0)>qd.get("callback_entry_ns",0) and qu.get("callback_entry_ns",0)>qd.get("callback_return_ns",0),{"producer":producer,"q_down":qd,"q_up":qu})
add("independent_same_generation_release",first_cancel.get("release_confirmed") is True and first_action.get("release_confirmed") is True and read.get("status")=="observed" and read.get("q_down") is False and read.get("generation_before")==gen==read.get("generation_after") and read.get("returned_monotonic_ns",0)>qd.get("callback_return_ns",0),{"cancel_release":first_cancel.get("release_confirmed"),"action_release":first_action.get("release_confirmed"),"readback":read})
pre_effect=R.get("effect_readback") or {}
add("pre_cancel_effect_is_distinct",pre_effect==trial["pre_recovery_effect"],{"actual":pre_effect,"expected":trial["pre_recovery_effect"]})
post_obs=(R.get("post_recovery_observation") or {}).get("raw_report") or {}
post_prog=R.get("post_recovery_program") or {}
post_trial=trial["post_recovery_program"]
add("fresh_post_recovery_observation_matches_generation",post_obs.get("target_generation")==gen and post_obs.get("status")=="returned" and post_obs.get("target_generation_consistency")=="matched",{"generation_before":gen,"observation":post_obs})
add("new_program_lease_and_dispatch_identity",post_prog.get("program_id")==post_trial["program_id"] and post_prog.get("authority",{}).get("lease_id")==post_trial["lease_id"] and post_prog.get("source",{}).get("observation_seq")==post_trial["observation_seq"] and post_prog.get("source",{}).get("binding_revision")==post_trial["binding_revision"] and (post_prog.get("source",{}).get("target_generations") or {}).get("fixture")==gen and isinstance(R.get("post_recovery_call_id"),str) and R.get("post_recovery_call_id")!=R.get("blocked_call_id"),{"program":post_prog,"first_call_id":R.get("blocked_call_id"),"new_call_id":R.get("post_recovery_call_id"),"attempts":R.get("post_recovery_dispatch_attempts")})
post_report=R.get("post_recovery_retained_report") or {}
post_action=((post_report.get("supervision") or {}).get("action") or {})
add("fresh_action_completed_after_recovery",R.get("post_recovery_dispatch_attempts")==1 and post_action.get("status")=="completed" and post_action.get("target_generation")==gen,{"action":post_action,"top_status":post_report.get("status")})
post_effect=R.get("post_recovery_effect_readback") or {}
add("post_recovery_effect_is_exact_and_persisted",post_effect==post_trial["expected_effect"],{"actual":post_effect,"expected":post_trial["expected_effect"]})
add("task_success_is_not_inferred",first.get("task_success") is None and post_report.get("task_success") is None and (post_report.get("result") or {}).get("task_success") is None,{"first_task_success":first.get("task_success"),"second_task_success":post_report.get("task_success"),"second_result":post_report.get("result")})
fixture=R.get("fixture") or {}
add("cleanup_and_no_emergency_input",fixture.get("exit_code")==0 and fixture.get("window_exists_after_exit") is False and hook.get("thread_exited") is True and (R.get("foreground_restore") or {}).get("restored") is True and R.get("emergency_q_up") is None and (R.get("session_close_report") or {}).get("status")=="closed",{"fixture_exit":fixture.get("exit_code"),"window_exists_after_exit":fixture.get("window_exists_after_exit"),"hook_exited":hook.get("thread_exited"),"foreground_restore":R.get("foreground_restore"),"emergency_q_up":R.get("emergency_q_up"),"close":R.get("session_close_report")})
status="PASS_SCOPED" if all(c["passed"] for c in checks) else "FAIL_OR_UNKNOWN"
out={"schema":"win32-supervised-standard-caller-r23-audit-v1","attempt_id":C["attempt_id"],"status":status,"passed":sum(c["passed"] for c in checks),"total":len(checks),"raw_sha256":hashlib.sha256((HERE/"raw.json").read_bytes()).hexdigest(),"checks":checks,"claims_excluded":C["claims_excluded"]}
(HERE/"audit.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"status":status,"passed":out["passed"],"total":out["total"],"failed":[c["name"] for c in checks if not c["passed"]]},sort_keys=True))
