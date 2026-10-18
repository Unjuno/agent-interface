"""Independent backward-context audit of the frozen V39 orphan ordering."""
import hashlib,json,urllib.request
COMMIT="c99d93a2c81945f0946173e48247bdd49e32a02a"; PATH="research/doom/results/v39-control-telemetry-gap-audit-20261004/events.jsonl"
URL=f"https://raw.githubusercontent.com/Unjuno/agent-interface/{COMMIT}/{PATH}"; EXPECTED="2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"
raw=urllib.request.urlopen(URL,timeout=20).read(); digest=hashlib.sha256(raw).hexdigest()
if digest!=EXPECTED: raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
events=[json.loads(x) for x in raw.splitlines()]
if len(events)!=634: raise SystemExit("STOP_ROW_COUNT_MISMATCH")
def context_at(i):
 starts=[(j,e) for j,e in enumerate(events[:i]) if e.get("event")=="step_started"]
 if not starts: return None
 j,start=starts[-1]; ident=start.get("id"); step=start.get("step")
 closed=any((e.get("event")=="step_completed" and e.get("id")==ident and e.get("step")==step) or (e.get("event")=="terminal" and e.get("id")==ident) or (e.get("event")=="cancel_requested" and e.get("id")==ident and e.get("matched") is True) for e in events[j+1:i])
 return None if closed else {"id":ident,"step":step,"operation":start.get("operation")}
admissions=[]
for i,e in enumerate(events):
 if e.get("event")=="input_admission":
  c=context_at(i)
  if c and c["operation"]=="hold": admissions.append({"index":i,"id":c["id"],"step":c["step"],"key":e.get("key"),"admitted_ns":e.get("admitted_ns"),"input_ack_ns":e.get("input_ack_ns")})
receipts=[(i,e) for i,e in enumerate(events) if e.get("event")=="keys_held"]
orphan=[]
for a in admissions:
 matches=[e for i,e in receipts if i>a["index"] and e.get("id")==a["id"] and e.get("step")==a["step"] and isinstance(e.get("keys"),list) and a["key"] in e["keys"]]
 if not matches: orphan.append(a)
if len(orphan)!=1 or orphan[0]!={"index":449,"id":"cover-4","step":10,"key":"Down","admitted_ns":55539824242850,"input_ack_ns":55539824580162}: raise SystemExit("FAIL_ORPHAN_RECONSTRUCTION "+json.dumps(orphan))
a=orphan[0]
cmd=next(e for e in events if e.get("event")=="command" and e.get("command",{}).get("op")=="cancel" and e.get("command",{}).get("id")==a["id"])
cancel=next(e for e in events if e.get("event")=="cancel_requested" and e.get("id")==a["id"] and e.get("matched") is True)
t=next(e for e in events if e.get("event")=="terminal" and e.get("id")==a["id"]); owner=t["interruption"]["record"]
checks={"admitted_before_cancel_command":a["admitted_ns"]<cmd["received_ns"],"ack_before_cancel_request":a["input_ack_ns"]<cancel["requested_ns"],"cleanup_after_ack":owner["verified_ns"]>a["input_ack_ns"],"empty_cleanup":owner["verified"] is True and owner["keys_down"]==[] and owner["buttons_down"]==[]}
if not all(checks.values()): raise SystemExit("FAIL_INDEPENDENT_AUDIT "+json.dumps(checks))
result={"status":"PASS_INDEPENDENT_TEMPORAL_AUDIT","source_sha256":digest,"rows":len(events),"orphan":a,"checks":checks,"delta_ns":{"cancel_command_minus_admitted":cmd["received_ns"]-a["admitted_ns"],"cancel_request_minus_ack":cancel["requested_ns"]-a["input_ack_ns"],"owner_cleanup_minus_ack":owner["verified_ns"]-a["input_ack_ns"]},"scope":"independent backward-context audit; no per-key up or physical/application delivery inferred"}
print(json.dumps(result,sort_keys=True))
