from pathlib import Path
import hashlib, json

HERE=Path(__file__).resolve().parent
raw=json.loads((HERE/"raw.json").read_text(encoding="utf-8"))
conditions=json.loads((HERE/"conditions.json").read_text(encoding="utf-8"))
hook=raw.get("hook_stopped") or {}
events=hook.get("events") or []
qdown=next((x for x in events if x.get("message")==256 and x.get("vk")==81),{})
qup=next((x for x in events if x.get("message")==257 and x.get("vk")==81),{})
producer=raw.get("producer_exit_witness") or {}
readback=raw.get("independent_readback") or {}
retained=raw.get("retained_report") or {}
supervision=retained.get("supervision") or {}
action=supervision.get("action") or {}
cancel=supervision.get("cancellation") or {}
close=raw.get("session_close_report") or {}
fixture=raw.get("fixture") or {}
effect=fixture.get("effect") or {}
checks=[]
def add(name,passed,evidence): checks.append({"name":name,"passed":bool(passed),"evidence":evidence})
add("one_dispatch_on_frozen_source",raw.get("dispatch_attempts")==1 and raw.get("source_tracked_tree_clean") is True and raw.get("source_commit")==conditions["source_commit"],{"dispatch_attempts":raw.get("dispatch_attempts"),"source_commit":raw.get("source_commit"),"tracked_clean":raw.get("source_tracked_tree_clean")})
add("post_cancel_callback_hold_forwarded",qdown.get("callback_return_ns",0)>qdown.get("callback_entry_ns",0) and raw.get("post_cancel_io_hold",{}).get("target_hold_ms")==250 and qdown.get("flags")==16,{"callback_entry_ns":qdown.get("callback_entry_ns"),"callback_return_ns":qdown.get("callback_return_ns"),"cancel_return_ns":(raw.get("public_cancel") or {}).get("returned_monotonic_ns"),"target_hold_ms":raw.get("post_cancel_io_hold",{}).get("target_hold_ms")})
identity=(cancel.get("result") or {}).get("producer_identity") or {}
add("exact_producer_retired_after_forward",producer.get("status")=="exited" and producer.get("pid")==identity.get("pid") and producer.get("creation_time_100ns")==identity.get("creation_time_100ns") and producer.get("observed_monotonic_ns",0)>=qdown.get("callback_return_ns",0),{"producer":producer,"callback_return_ns":qdown.get("callback_return_ns")})
generation=(fixture.get("target_identity") or {}).get("generation")
add("same_generation_q_up_and_independent_neutral_readback",qup.get("callback_entry_ns",0)>qdown.get("callback_return_ns",0) and readback.get("status")=="observed" and readback.get("q_down") is False and readback.get("generation_before")==generation==readback.get("generation_after") and readback.get("returned_monotonic_ns",0)>qdown.get("callback_return_ns",0),{"q_up":qup,"readback":readback})
add("cancel_recovered_release_receipt",cancel.get("status")=="recovered" and cancel.get("release_confirmed") is True and cancel.get("target_generation")==action.get("target_generation"),{"status":cancel.get("status"),"release_confirmed":cancel.get("release_confirmed"),"generation":cancel.get("target_generation")})
result=action.get("result") or {}
add("repaired_public_action_terminal_and_replay_denied",action.get("status")=="recovered" and result.get("status")=="recovered" and result.get("release_confirmed") is True and result.get("effect_status")=="unknown" and result.get("input_dispatched") is None and result.get("task_success") is None and result.get("replay_allowed") is False,{"action":action})
add("fixture_effect_and_cleanup",effect.get("clicked") is True and effect.get("saved") is True and effect.get("text")==conditions["trial"]["expected_effect"]["text"] and fixture.get("exit_code")==0 and fixture.get("window_exists_after_exit") is False and hook.get("thread_exited") is True,{"effect":effect,"fixture_exit":fixture.get("exit_code"),"window_exists_after_exit":fixture.get("window_exists_after_exit"),"hook_exited":hook.get("thread_exited"),"foreground_restore":raw.get("foreground_restore")})
add("task_success_remains_unknown",retained.get("task_success") is None and result.get("task_success") is None and result.get("effect_status")=="unknown",{"task_success":retained.get("task_success"),"effect_status":result.get("effect_status")})
add("close_receipt_discrepancy_preserved",close.get("status")=="closed" and close.get("release_confirmed") is False and cancel.get("release_confirmed") is True,{"close_status":close.get("status"),"close_release_confirmed":close.get("release_confirmed"),"cancel_release_confirmed":cancel.get("release_confirmed")})
status="PARTIAL" if all(x["passed"] for x in checks) else "FAIL_OR_UNKNOWN"
out={"schema":"win32-supervised-standard-caller-r22-additive-audit-v1","attempt_id":conditions["attempt_id"],"status":status,"checks_passed":sum(x["passed"] for x in checks),"checks_total":len(checks),"raw_sha256":hashlib.sha256((HERE/"raw.json").read_bytes()).hexdigest(),"checks":checks,"interpretation":"A terminal recovered action agrees with the cancellation custody generation and release receipt. Independent same-generation readback observed Q-up after callback return. The exact fixture effect predates cancel, so runtime task_success remains null. Close reports closed with release_confirmed=false while cancellation reports release_confirmed=true; preserve this discrepancy and classify this attempt PARTIAL."}
(HERE/"audit_repair_followup.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"status":status,"passed":out["checks_passed"],"total":len(checks)},sort_keys=True))
