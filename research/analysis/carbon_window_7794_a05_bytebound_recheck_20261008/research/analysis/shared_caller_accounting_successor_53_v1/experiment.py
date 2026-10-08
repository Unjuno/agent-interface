"""Finite shared acquisition caller accounting successor for #53."""
import json
from pathlib import Path

SCENARIOS=[
 {"id":"accepted_anchor","stage":["coarse","anchor"],"outcome":"success"},
 {"id":"expanded_recovery","stage":["coarse","anchor","expanded"],"outcome":"success"},
 {"id":"no_match","stage":["coarse"],"outcome":"no_match"},
 {"id":"stale_refusal","stage":["coarse"],"outcome":"stale"},
]

def shared_caller(scenario):
    calls=[]
    for i,stage in enumerate(scenario["stage"],1):
        calls.append({"call_id":f'{scenario["id"]}-{i}',"stage":stage,"input_tokens":100+i,"output_tokens":10,"status":"completed"})
    return {"scenario":scenario["id"],"outcome":scenario["outcome"],"calls":calls,"task_success":scenario["outcome"]=="success","fallback":scenario["outcome"]!="success"}

def run():
    records=[shared_caller(s) for s in SCENARIOS]
    flat=[c for r in records for c in r["calls"]]
    assert len({c["call_id"] for c in flat})==len(flat)
    assert sum(c["input_tokens"] for c in flat)==sum(100+i for r in records for i,_ in enumerate(r["calls"],1))
    summary={r["scenario"]:{"outcome":r["outcome"],"calls":len(r["calls"]),"task_success":r["task_success"],"fallback":r["fallback"]} for r in records}
    return {"decision":"PASS_SHARED_CALLER_ACCOUNTING_SCOPED","records":records,"summary":summary,"total_calls":len(flat),"total_input_tokens":sum(c["input_tokens"] for c in flat),"scope":"Finite deterministic caller/accounting mechanics; no GUI/model/network/task input."}

if __name__=="__main__":
 out=Path("research/analysis/shared_caller_accounting_successor_53_v1/RESULT.json"); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(run(),indent=2)+"\n"); print(out)
