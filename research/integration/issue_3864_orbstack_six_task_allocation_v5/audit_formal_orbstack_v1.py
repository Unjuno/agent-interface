"""Independent raw-evidence audit for the finite OrbStack allocation."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"research/live_control"))
from integrated_efficiency_protocol_v1 import ARMS, evaluate
OUT=Path(sys.argv[1]); INNER=OUT/"formal-output"
trace=json.loads((INNER/"trace.json").read_text())
recomputed=evaluate(trace)
reported=json.loads((INNER/"evaluation.json").read_text())
if recomputed!=reported: raise SystemExit("FAIL_SCORER_DISAGREEMENT")
requests=sorted(OUT.glob("ipc/request-*/*.request.json"))
responses=sorted(OUT.glob("ipc/request-*/*.response.jsonl"))
receipts=sorted(OUT.glob("ipc/request-*/*.broker.json"))
if not (len(requests)==len(responses)==len(receipts)==17): raise SystemExit("FAIL_RAW_CALL_COUNTS")
call_ids=[]; call_audit=[]
for req_path in requests:
    req=json.loads(req_path.read_text()); folder=req_path.parent
    response=folder/(req["request_id"]+".response.jsonl")
    receipt=folder/(req["request_id"]+".broker.json")
    broker=json.loads(receipt.read_text())
    rows=[json.loads(line) for line in response.read_text().splitlines() if line]
    messages=[r["item"] for r in rows if r.get("type")=="item.completed" and r.get("item",{}).get("type")=="agent_message"]
    turns=[r for r in rows if r.get("type")=="turn.completed"]
    threads=[r.get("thread_id") for r in rows if r.get("type")=="thread.started"]
    if len(messages)!=1 or len(turns)!=1 or len(threads)!=1 or not turns[0].get("usage"):
        raise SystemExit("FAIL_EVENT_CARDINALITY:"+req["request_id"])
    if broker.get("host_cli_invoked") is not True or broker.get("returncode")!=0 or broker.get("authority_granted") is not False:
        raise SystemExit("FAIL_BROKER_RECEIPT:"+req["request_id"])
    call_ids += threads
    call_audit.append({"request_id":req["request_id"],"mode":req["mode"],"image_sha256":req.get("image_sha256"),
        "thread_id":threads[0],"usage":turns[0]["usage"],"raw_sha256":__import__("hashlib").sha256(response.read_bytes()).hexdigest()})
if len(set(call_ids))!=17: raise SystemExit("FAIL_CALL_ID_UNIQUENESS")
if sum(x["mode"]=="handle" for x in call_audit)!=3 or sum(x["mode"]=="coordinate" for x in call_audit)!=14:
    raise SystemExit("FAIL_MODE_SCHEDULE")
trace_ids=[row["call_id"] for arm in ARMS for row in trace["arms"][arm]
    for row in row["model_calls"]]
trace_ids += [trace["preflight_calls"][arm]["call_id"] for arm in ARMS]
if set(trace_ids)!=set(call_ids) or len(trace_ids)!=17: raise SystemExit("FAIL_RAW_TRACE_CALL_MAPPING")
history_audits={}
for arm in ARMS:
    history_path=INNER/"arms"/arm/"runtime/submission-history.jsonl"
    history=[json.loads(line) for line in history_path.read_text().splitlines()] if history_path.exists() else []
    counts={f"task-{i}":0 for i in range(1,7)}; exact={key:True for key in counts}
    for row in history:
        tid=row.get("task_id")
        if tid in counts: counts[tid]+=1; exact[tid] &= row.get("exact") is True
    if len(history)!=6 or not all(counts[t]==1 and exact[t] for t in counts): raise SystemExit("FAIL_ORACLE_HISTORY:"+arm)
    for row in trace["arms"][arm]:
        if row["typed_outcome"]!="completed" or not row["releases_verified"] or not row["exact_submission"]:
            raise SystemExit("FAIL_TASK_OR_RELEASE:"+arm+":"+row["task_id"])
    history_audits[arm]={"counts":counts,"records":len(history)}
result={"status":"PASS_INDEPENDENT_RAW_AUDIT","host_model_calls":17,"unique_thread_ids":len(set(call_ids)),
    "preflights":3,"coordinate_calls":14,"arms":history_audits,
    "disposition":recomputed["disposition"],"calls":call_audit}
(OUT/"independent-audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":result["status"],"disposition":result["disposition"],"calls":17},sort_keys=True))
