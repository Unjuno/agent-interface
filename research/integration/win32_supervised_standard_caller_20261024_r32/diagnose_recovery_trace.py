"""Pair R31 recovery boundary events against the native-hook callback return."""
from __future__ import annotations
import json
from pathlib import Path
P = Path(__file__).resolve().parent
raw = json.loads((P / "raw.json").read_text(encoding="utf-8"))
events_path = P / "run" / "cancellation_call_trace.jsonl"
events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
callback_end = raw.get("post_cancel_io_hold", {}).get("hook_trace_before_release", {}).get("callback_return_ns")
if type(callback_end) is not int:
    callback_end = raw.get("hook_stopped", {}).get("callback_return_ns")
helper_roles = {row.get("pid"): row.get("helper") for row in events if row.get("event") == "helper_enter"}
open_spans = []
def pair(start_event, end_events, identity):
    starts = [e for e in events if e.get("event") == start_event]
    for start in starts:
        key = (start.get("pid"), start.get(identity))
        ends = [e for e in events if e.get("event") in end_events
                and (e.get("pid"), e.get(identity)) == key
                and e.get("monotonic_ns", 0) >= start.get("monotonic_ns", 0)]
        end = min(ends, key=lambda e:e["monotonic_ns"]) if ends else None
        span = {"boundary":start_event.removesuffix("_enter"), "pid":start.get("pid"),
                "helper_role":helper_roles.get(start.get("pid")),
                "start_ns":start.get("monotonic_ns"),
                "end_ns":end.get("monotonic_ns") if end else None,
                "elapsed_ns":end.get("elapsed_ns") if end else None,
                "end_event":end.get("event") if end else None,
                "identity":start.get(identity)}
        if end is None or (type(callback_end) is int and start.get("monotonic_ns", 0) <= callback_end < end.get("monotonic_ns", 0)):
            open_spans.append(span)
        return_span.append(span)

return_span=[]
pair("exchange_enter", {"exchange_return", "exchange_exception"}, "request_id")
pair("recover_enter", {"recover_return", "recover_exception"}, "recovery_id")
# release_all and SendInput calls are ordered within each exact process; pair by per-process event order.
def pair_ordered(start_event, end_events, qualifier=None):
    for pid in sorted({e.get("pid") for e in events}):
        stack=[]
        for event in [e for e in events if e.get("pid")==pid]:
            if event.get("event")==start_event and (qualifier is None or qualifier(event)):
                stack.append(event)
            elif event.get("event") in end_events and stack:
                start=stack.pop(0)
                span={"boundary":start_event.removesuffix("_enter"),"pid":pid,
                      "helper_role":helper_roles.get(pid),"start_ns":start.get("monotonic_ns"),
                      "end_ns":event.get("monotonic_ns"),"elapsed_ns":event.get("elapsed_ns"),
                      "end_event":event.get("event"),"input":{k:start.get(k) for k in ("vk","key_up","flags") if k in start}}
                return_span.append(span)
                if type(callback_end) is int and start.get("monotonic_ns",0)<=callback_end<event.get("monotonic_ns",0): open_spans.append(span)
        for start in stack:
            span={"boundary":start_event.removesuffix("_enter"),"pid":pid,
                  "helper_role":helper_roles.get(pid),"start_ns":start.get("monotonic_ns"),
                  "end_ns":None,"elapsed_ns":None,"end_event":None,
                  "input":{k:start.get(k) for k in ("vk","key_up","flags") if k in start}}
            return_span.append(span); open_spans.append(span)
pair_ordered("release_all_enter", {"release_all_return", "release_all_exception"})
pair_ordered("sendinput_enter", {"sendinput_return", "sendinput_exception"},
             lambda e:e.get("key_up") is True and e.get("vk")==ord("Q"))
result={"schema":"win32-supervised-standard-caller-r31-recovery-trace-diagnosis-v1",
        "attempt_id":"win32-supervised-standard-caller-20261024-r31",
        "diagnostic_status":"TRACE_CAPTURED" if callback_end else "FAIL_OR_UNKNOWN",
        "callback_return_ns":callback_end,
        "event_count":len(events),"helper_processes":helper_roles,
        "boundary_spans":return_span,"open_at_or_across_callback_return":open_spans,
        "interpretation":"The trace locates Python helper and _send boundaries relative to the callback return. It cannot show when the OS physically applied a key-up or establish kernel causality; missing wrapper events or cross-process timestamp effects remain diagnostic limitations.",
        "strict_action_audit_status":json.loads((P/"audit.json").read_text(encoding="utf-8")).get("status")}
(P/"recovery_trace_diagnosis.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"diagnostic_status":result["diagnostic_status"],"event_count":len(events),"helper_processes":len(helper_roles),"open_across_callback":len(open_spans),"audit":result["strict_action_audit_status"]},sort_keys=True))