#!/usr/bin/env python3
"""Independent recursive reconstruction of the A03 comparator diagnostic."""
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).parent


def recursive_assignments(jobs):
    out=[]
    def visit(i, schedule, occupied):
        if i==len(jobs):
            out.append(dict(schedule)); return
        job=jobs[i]
        lo=max([job["release"]]+[schedule[p]+next(q["duration"] for q in jobs if q["id"]==p) for p in job["predecessors"]])
        hi=min(job["deadline"],job["fresh_until"])-job["duration"]
        for start in range(lo,hi+1):
            ticks=frozenset(range(start,start+job["duration"]))
            if occupied.isdisjoint(ticks):
                schedule[job["id"]]=start
                visit(i+1,schedule,occupied|ticks)
                del schedule[job["id"]]
    visit(0,{},frozenset())
    return out


def independent_serial(jobs):
    result={}; used=set()
    for j in jobs:
        bound=j["release"]
        for pred in j["predecessors"]:
            parent=next(x for x in jobs if x["id"]==pred)
            bound=max(bound,result[pred]+parent["duration"])
        start=next((s for s in range(bound,min(j["deadline"],j["fresh_until"])-j["duration"]+1)
                    if all(t not in used for t in range(s,s+j["duration"]))),None)
        if start is None: return None
        result[j["id"]]=start
        used.update(range(start,start+j["duration"]))
    return result


def main():
    source=json.loads((ROOT/"a02_frozen_cases.json").read_text())
    cases=list(source["cases"])+[{"id":"priority_deadend_discriminator","jobs":[
        {"id":"A","duration":1,"release":0,"deadline":3,"fresh_until":3,"predecessors":[],"cancelled":False},
        {"id":"B","duration":1,"release":0,"deadline":1,"fresh_until":1,"predecessors":[],"cancelled":False}]}]
    candidate=json.loads((ROOT/"formal_a03/candidate.json").read_text())
    expected=[]
    for c in cases:
        jobs=[j for j in c["jobs"] if not j["cancelled"]]
        schedules=recursive_assignments(jobs)
        global_pick=min(schedules,key=lambda s:tuple(s[j["id"]] for j in jobs)) if schedules else None
        serial=independent_serial(jobs)
        expected.append({"case_id":c["id"],"feasible_count":len(schedules),"global_lexicographic":global_pick,"serial_asap":serial,"same":global_pick==serial})
    errs=[]
    if candidate.get("input_sha256")!=hashlib.sha256((ROOT/"a02_frozen_cases.json").read_bytes()).hexdigest(): errs.append("input_digest")
    if candidate.get("rows")!=expected: errs.append("independent_reconstruction")
    if len(expected)!=10: errs.append("case_count")
    if not all(r["same"] for r in expected[:9]): errs.append("unexpected_A02_case_divergence")
    if expected[-1]["same"] or expected[-1]["global_lexicographic"]!={"A":1,"B":0} or expected[-1]["serial_asap"] is not None: errs.append("discriminator_missing")
    audit={"status":"PASS_DIAGNOSTIC_SCOPED" if not errs else "FAIL_AUDIT","cases_reconstructed":len(expected),"a02_differences":sum(not r["same"] for r in expected[:9]),"discriminator":expected[-1],"errors":errs}
    print(json.dumps(audit,sort_keys=True,indent=2))
    if errs: raise SystemExit(1)


if __name__=="__main__": main()
