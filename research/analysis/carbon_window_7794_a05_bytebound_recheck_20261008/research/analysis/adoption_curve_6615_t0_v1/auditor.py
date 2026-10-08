"""Separate reconstruction of first-use cost and verified-effect denominators."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


def expected_rows(fixture: dict) -> list[dict]:
    result = []
    for s in fixture["scenarios"]:
        for route in ("direct", "guarded"):
            st = s[route + "_setup"]
            total_w, total_a, successes = st["wall_s"], st["active_s"], 0
            result.append({"scenario":s["id"],"route":route,"prefix":0,
                "event":"SETUP_SUCCESS" if st["success"] else "SETUP_FAILURE",
                "task_id":None,"wall_s":total_w,"active_s":total_a,
                "verified_useful":False,"cumulative_wall_s":total_w,
                "cumulative_active_s":total_a,"verified_count":0,"supported":s["supported"]})
            for n, task in enumerate(s["tasks"],1):
                arm=task[route]
                if not st["success"] or not s["supported"]:
                    event,w,a,good="BLOCKED_SETUP_OR_UNSUPPORTED_HOST",0,0,False
                elif arm["eligible"] is False:
                    event,w,a,good="ROUTE_INELIGIBLE",arm["wall_s"],arm["active_s"],False
                else:
                    repair=task.get("repair_before",{}) if route=="guarded" else {}
                    w=arm["wall_s"]+repair.get("wall_s",0)
                    a=arm["active_s"]+repair.get("active_s",0)
                    good=arm["correct"] is True
                    event="VERIFIED_USEFUL" if good else "ATTEMPTED_WRONG_OR_UNVERIFIED_EFFECT"
                total_w+=w; total_a+=a; successes+=int(good)
                result.append({"scenario":s["id"],"route":route,"prefix":n,
                    "event":event,"task_id":task["id"],"wall_s":w,"active_s":a,
                    "verified_useful":good,"cumulative_wall_s":total_w,
                    "cumulative_active_s":total_a,"verified_count":successes,
                    "supported":s["supported"]})
    return result


def inspect(fixture: dict, raw: list[dict]) -> dict:
    expected=expected_rows(fixture); errors=[]
    if raw!=expected: errors.append("raw-ledger-reconstruction-mismatch")
    keys=[(r["scenario"],r["route"],r["prefix"]) for r in raw]
    if len(keys)!=len(set(keys)): errors.append("duplicate-row-key")
    if any(r["verified_useful"] and (not r["supported"] or r["event"]!="VERIFIED_USEFUL") for r in raw):
        errors.append("unsupported-or-invalid-counted-as-success")
    if any(r["event"]=="SETUP_FAILURE" and r["verified_count"]!=0 for r in raw):
        errors.append("setup-failure-counted-as-useful-work")
    if any(r["route"]=="guarded" and r["scenario"]=="no_followup" and r["prefix"]==0 and r["cumulative_wall_s"]==0 for r in raw):
        errors.append("no-followup-setup-cost-dropped")
    crossings=[]
    ids={s["id"] for s in fixture["scenarios"]}
    for sid in sorted(ids):
        d=[r for r in raw if r["scenario"]==sid and r["route"]=="direct"]
        g=[r for r in raw if r["scenario"]==sid and r["route"]=="guarded"]
        byprefix={r["prefix"]:r for r in g}
        points=[]
        for dr in d:
            gr=byprefix.get(dr["prefix"])
            if gr is None:
                errors.append(f"missing-guarded-prefix:{sid}:{dr['prefix']}")
                continue
            identical=(dr["verified_count"]==dr["prefix"] and gr["verified_count"]==gr["prefix"])
            points.append({"prefix":dr["prefix"],"direct_wall_s":dr["cumulative_wall_s"],
                "guarded_wall_s":gr["cumulative_wall_s"],"direct_active_s":dr["cumulative_active_s"],
                "guarded_active_s":gr["cumulative_active_s"],"quality_comparable":identical})
        eligible=[p for p in points if p["quality_comparable"]]
        first=next((p["prefix"] for p in eligible if p["guarded_wall_s"]<=p["direct_wall_s"]),None)
        crossings.append({"scenario":sid,"first_comparable_wall_break_even_prefix":first,"points":points})
    return {"errors":errors,"rows":len(raw),"expected_rows":len(expected),
        "setup_failures":sum(r["event"]=="SETUP_FAILURE" and r["supported"] for r in raw),
        "wrong_or_unverified_attempts":sum(r["event"]=="ATTEMPTED_WRONG_OR_UNVERIFIED_EFFECT" for r in raw),
        "route_ineligible_attempts":sum(r["event"]=="ROUTE_INELIGIBLE" for r in raw),
        "unsupported_host_successes":sum(r["verified_useful"] and not r["supported"] for r in raw),
        "crossings":crossings}


def corrupt(raw: list[dict], kind: str) -> list[dict]:
    x=copy.deepcopy(raw)
    if kind=="drop_setup_failure": x=[r for r in x if not (r["scenario"]=="setup_failure" and r["route"]=="guarded" and r["prefix"]==0)]
    elif kind=="attempt_as_success":
        next(r for r in x if r["scenario"]=="candidate_wrong_effect" and r["route"]=="guarded" and r["prefix"]==2)["verified_useful"]=True
    elif kind=="unsupported_success":
        next(r for r in x if r["scenario"]=="unsupported_host" and r["route"]=="guarded" and r["prefix"]==1)["verified_useful"]=True
    elif kind=="drop_setup_cost":
        next(r for r in x if r["scenario"]=="setup_dominates" and r["route"]=="guarded" and r["prefix"]==0)["cumulative_wall_s"]=0
    elif kind=="repair_free":
        r=next(r for r in x if r["scenario"]=="app_change_repair" and r["route"]=="guarded" and r["prefix"]==3)
        r["wall_s"]-=30; r["cumulative_wall_s"]-=30
    return x


def main() -> None:
    fixture=json.loads(Path(sys.argv[1]).read_text())
    raw=json.loads(Path(sys.argv[2]).read_text())
    out=inspect(fixture,raw)
    print(json.dumps(out,sort_keys=True,separators=(",",":")))
    raise SystemExit(0 if not out["errors"] else 1)


if __name__=="__main__": main()
