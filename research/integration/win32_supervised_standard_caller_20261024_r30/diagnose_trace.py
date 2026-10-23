"""Independent R30 diagnosis of the exact producer retirement call trace."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent; C=json.loads((P/"conditions.json").read_text()); R=json.loads((P/"raw.json").read_text()); rows=R.get("cancellation_call_trace",[]); pid=(R.get("producer_identity_from_cancel") or {}).get("pid"); events=[x for x in rows if x.get("target_pid")==pid]; enter=next((x for x in events if x.get("event")=="retire_enter"),None); exits=[x for x in events if x.get("event")=="retire_return"]; methods=[]
for row in events:
 if row.get("event") in ("process_method_enter","process_method_return","process_method_exception"):
  methods.append({"event":row["event"],"method":row.get("method"),"monotonic_ns":row.get("monotonic_ns"),"elapsed_ns":row.get("elapsed_ns"),"args_repr":row.get("args_repr"),"result_repr":row.get("result_repr"),"error":row.get("error")})
callback_return=(R.get("hook_stopped") or {}).get("callback_return_ns"); hold_end=(R.get("post_cancel_io_hold") or {}).get("ended_monotonic_ns"); classifications=[]
for i,row in enumerate(methods):
 if row["event"]=="process_method_enter":
  later=next((x for x in methods[i+1:] if x["event"] in ("process_method_return","process_method_exception") and x["method"]==row["method"]),None)
  if later and type(callback_return) is int and row["monotonic_ns"]<callback_return<later["monotonic_ns"]:
   classifications.append({"method":row["method"],"entry":row["monotonic_ns"],"return":later["monotonic_ns"],"callback_return":callback_return,"classification":"call_spans_callback_return"})
coverage=bool(enter and any(x.get("event")=="retire_return" for x in events) and {x.get("method") for x in methods if x["event"]=="process_method_enter"})
out={"schema":"win32-supervised-standard-caller-r30-retirement-trace-diagnosis-v1","attempt_id":C["attempt_id"],"exact_producer_pid":pid,"diagnostic_status":"TRACE_CAPTURED" if enter and methods else "TRACE_INCOMPLETE","retire_entry":enter,"retire_return_count":len(exits),"method_events":methods,"calls_spanning_callback_return":classifications,"hook_callback_return_ns":callback_return,"post_cancel_hold_end_ns":hold_end,"raw_trace_event_count":len(rows),"strict_action_audit_status":json.loads((P/"audit.json").read_text()).get("status"),"interpretation":"Trace identifies which Python process retirement API call spans callback return; it does not establish earlier key release, OS kernel causality, or release while blocked."}
(P/"retirement_trace_diagnosis.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps({"diagnostic_status":out["diagnostic_status"],"exact_pid":pid,"method_entries":sum(x["event"]=="process_method_enter" for x in methods),"spans_callback_return":classifications},sort_keys=True)); raise SystemExit(0 if coverage else 1)
