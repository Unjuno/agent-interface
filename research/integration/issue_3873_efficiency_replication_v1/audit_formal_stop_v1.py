"""Independent audit of a pre-task broker STOP; makes no model calls."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
OUT=Path(sys.argv[1]).resolve()
ROOT=Path(__file__).resolve().parents[3]
def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
launcher=read(OUT/"launcher-result.json")
requests=sorted(OUT.glob("ipc/request-*/*.request.json"))
responses=sorted(OUT.glob("ipc/request-*/*.response.jsonl"))
receipts=sorted(OUT.glob("ipc/request-*/*.broker.json"))
assert launcher["status"]=="STOP_BROKER_FAILURE"
assert len(requests)==2 and len(responses)==1 and len(receipts)==1
first=read(requests[0]);broker=read(receipts[0])
rows=[json.loads(x) for x in responses[0].read_text().splitlines() if x]
threads=[x.get("thread_id") for x in rows if x.get("type")=="thread.started"]
messages=[x for x in rows if x.get("type")=="item.completed" and x.get("item",{}).get("type")=="agent_message"]
turns=[x for x in rows if x.get("type")=="turn.completed"]
assert first["mode"]=="handle" and first["image"] is None and first["authority_granted"] is False
assert len(threads)==len(messages)==len(turns)==1 and turns[0].get("usage")
assert broker["boundary"]=="host-local-codex-exe" and broker["returncode"]==0
assert broker["authority_granted"] is False
assert launcher["broker_invocations"]==1 and launcher["broker_results"][0]["returncode"]==1
assert not list((OUT/"ipc/request-02").glob("*.response.jsonl"))
assert not list((OUT/"ipc/request-02").glob("*.broker.json"))
assert not list((OUT/"formal-output").glob("trace.json"))
assert not list((OUT/"formal-output").glob("arms/**/submission-history.jsonl"))
broker_source=(ROOT/"runtime/host_model_ipc_broker_v1.py").read_text()
assert "return broker.get(\"returncode\") or 1" in broker_source
result={"status":"STOP_INDEPENDENTLY_CONFIRMED_BROKER_ZERO_EXIT_MISREPORTED",
 "host_model_calls":1,"completed_schema_preflights":1,"task_calls":0,
 "ipc_requests_emitted":2,"host_responses":1,"broker_receipts":1,"retries":0,
 "successful_host_cli_returncode":broker["returncode"],"broker_process_returncode":launcher["broker_results"][0]["returncode"],
 "thread_id":threads[0],"usage":turns[0]["usage"],"authority_granted":False,
 "schema_validation":read(OUT/"requests/request-01/schema-validation.json")["status"],
 "root_cause":"serve(..., once=True) returns broker.get(\"returncode\") or 1; successful returncode 0 is coerced to process exit 1.",
 "raw_sha256":{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob("*")) if p.is_file()
               and p.name not in {"STOP.json","STOP_REPORT.md","independent-stop-audit.json"}}}
(OUT/"independent-stop-audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:result[k] for k in ("status","host_model_calls","task_calls","root_cause")},sort_keys=True))
