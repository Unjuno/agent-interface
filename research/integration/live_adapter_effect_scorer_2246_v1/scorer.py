"""Independent, read-only scorer for a retained golden desktop report.

This tool never launches a model, GUI, input device, or network client. It scores
serialized evidence only. Live authority is an explicit gate and never inferred.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

SCHEMA="live_adapter_effect_score_v1"
REQUIRED_ROUTES={"cold","reuse","repair"}

def score(report: dict, *, live_authority: bool=False) -> dict:
    checks=[]
    def check(name, ok, detail):
        checks.append({"name":name,"passed":bool(ok),"detail":detail})
    check("schema", report.get("schema")=="agent_interface_golden_desktop_live_v2", str(report.get("schema")))
    tasks=report.get("tasks")
    check("tasks_exact", report.get("tasks_exact")==6 and isinstance(tasks,list) and len(tasks)==6,
          f"declared={report.get('tasks_exact')} actual={len(tasks) if isinstance(tasks,list) else 'not-list'}")
    check("routes", isinstance(report.get("routes"),list) and REQUIRED_ROUTES.issubset(set(report["routes"])),
          repr(report.get("routes")))
    oracle=report.get("independent_evaluation") or {}
    check("independent_evaluation", oracle.get("success") is True and oracle.get("record_count")==6
          and oracle.get("unexpected")==[] and oracle.get("missing")==[],
          "oracle success/count/unexpected/missing")
    check("task_outcomes", all(isinstance(t,dict) and t.get("typed_outcome")=="completed"
          and t.get("exact_submission") is True for t in tasks) if isinstance(tasks,list) else False,
          "all six completed with exact submission")
    check("release_cleanup", report.get("all_releases_verified") is True
          and all(t.get("releases_verified") is True for t in tasks) if isinstance(tasks,list) else False,
          "all releases verified")
    failures=[c["name"] for c in checks if not c["passed"]]
    if failures:
        status="FAIL"
        reason="INVALID_EVIDENCE:"+",".join(failures)
    elif not live_authority:
        status="HOLD"
        reason="HOLD_NO_MODEL_AUTHORITY"
    else:
        status="PASS"
        reason="LIVE_AUTHORITY_DECLARED_BUT_NOT_EXECUTED_BY_SCORER"
    return {"schema":SCHEMA,"status":status,"reason":reason,
            "authority_granted":bool(live_authority),"checks":checks,
            "scope":"serialized evidence only; scorer performs no model/GUI/input/network action"}

def main(argv=None)->int:
    p=argparse.ArgumentParser()
    p.add_argument("report",type=Path)
    p.add_argument("--live-authority",action="store_true",
                   help="record an external authority gate; does not execute live work")
    args=p.parse_args(argv)
    try:
        report=json.loads(args.report.read_text(encoding="utf-8"))
    except Exception as e:
        json.dump({"schema":SCHEMA,"status":"FAIL","reason":"REPORT_READ_ERROR:"+type(e).__name__},sys.stdout)
        return 2
    result=score(report,live_authority=args.live_authority)
    json.dump(result,sys.stdout,sort_keys=True); sys.stdout.write("\n")
    return 0 if result["status"] in {"PASS","HOLD"} else 1

if __name__=="__main__":
    raise SystemExit(main())
