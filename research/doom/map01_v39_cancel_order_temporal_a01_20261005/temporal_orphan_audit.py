"""Posthoc temporal ordering audit for the frozen V39 unmatched admission."""
import hashlib, json, urllib.request
SOURCE_COMMIT="c99d93a2c81945f0946173e48247bdd49e32a02a"
SOURCE_PATH="research/doom/results/v39-control-telemetry-gap-audit-20261004/events.jsonl"
URL=f"https://raw.githubusercontent.com/Unjuno/agent-interface/{SOURCE_COMMIT}/{SOURCE_PATH}"
EXPECTED="2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"
raw=urllib.request.urlopen(URL,timeout=20).read(); actual=hashlib.sha256(raw).hexdigest()
if actual!=EXPECTED: raise SystemExit("STOP_SOURCE_HASH_MISMATCH "+actual)
events=[json.loads(line) for line in raw.splitlines()]
if len(events)!=634: raise SystemExit("STOP_ROW_COUNT_MISMATCH")
scope=None; admissions=[]; receipts=[]
for i,e in enumerate(events):
 k=e.get("event")
 if k=="step_started": scope={"id":e.get("id"),"step":e.get("step"),"operation":e.get("operation")}
 elif k=="input_admission" and scope and scope["operation"]=="hold": admissions.append({"index":i,"id":scope["id"],"step":scope["step"],"key":e.get("key"),"admitted_ns":e.get("admitted_ns"),"input_ack_ns":e.get("input_ack_ns")})
 elif k=="keys_held": receipts.append({"index":i,"id":e.get("id"),"step":e.get("step"),"keys":e.get("keys")})
 elif k=="step_completed" and scope and e.get("id")==scope["id"] and e.get("step")==scope["step"]: scope=None
 elif k=="terminal" and scope and e.get("id")==scope["id"]: scope=None
 elif k=="cancel_requested" and scope and e.get("id")==scope["id"] and e.get("matched") is True: scope=None
unmatched=[a for a in admissions if not any(r["id"]==a["id"] and r["step"]==a["step"] and r["index"]>a["index"] and a["key"] in (r["keys"] or []) for r in receipts)]
if len(unmatched)!=1 or (unmatched[0]["id"],unmatched[0]["step"],unmatched[0]["key"])!=("cover-4",10,"Down"): raise SystemExit("STOP_UNEXPECTED_UNMATCHED "+json.dumps(unmatched))
a=unmatched[0]
cmd=next(e for e in events if e.get("event")=="command" and e.get("command",{}).get("op")=="cancel" and e.get("command",{}).get("id")==a["id"])
cr=next(e for e in events if e.get("event")=="cancel_requested" and e.get("id")==a["id"] and e.get("matched") is True)
t=next(e for e in events if e.get("event")=="terminal" and e.get("id")==a["id"]); owner=t["interruption"]["record"]
checks={"admission_precedes_cancel_command":a["admitted_ns"]<cmd["received_ns"],"ack_precedes_cancel_request":a["input_ack_ns"]<cr["requested_ns"],"owner_cleanup_follows_ack":owner["verified_ns"]>a["input_ack_ns"],"terminal_release_follows_ack":t["release"]["verified_ns"]>a["input_ack_ns"],"cleanup_empty":owner["verified"] is True and owner["keys_down"]==[] and owner["buttons_down"]==[]}
if not all(checks.values()): raise SystemExit("FAIL_TEMPORAL_ORDER "+json.dumps(checks))
print(json.dumps({"status":"PASS_TEMPORAL_ORDERING_ONLY","source_commit":SOURCE_COMMIT,"source_sha256":actual,"rows":len(events),"admission":a,"cancel_command_received_ns":cmd["received_ns"],"matched_cancel_requested_ns":cr["requested_ns"],"owner_cleanup_verified_ns":owner["verified_ns"],"terminal_release_verified_ns":t["release"]["verified_ns"],"deltas_ns":{"cancel_command_minus_admitted":cmd["received_ns"]-a["admitted_ns"],"cancel_request_minus_input_ack":cr["requested_ns"]-a["input_ack_ns"],"owner_cleanup_minus_input_ack":owner["verified_ns"]-a["input_ack_ns"],"terminal_release_minus_input_ack":t["release"]["verified_ns"]-a["input_ack_ns"]},"checks":checks,"candidate_execution_count":0,"formal_allocation_count":0,"retries":0,"scope":"posthoc timestamps/ledgers only; not key-up, physical occupancy, app delivery, useful feedback, recovery, or causal benefit"},sort_keys=True))
