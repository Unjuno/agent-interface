"""Interval-demand oracle candidate for Issue #7748's finite method rung."""
from functools import lru_cache
import json, sys

REQUIRED=("id","class","release","execution","deadline","preemptible")

def demand(jobs):
    if not jobs:
        return {"feasible":True,"max_excess":0,"witnesses":[]}
    points=sorted({j["release"] for j in jobs}|{j["deadline"] for j in jobs})
    excesses=[]
    for a in points:
        for b in points:
            if b<=a: continue
            work=sum(j["execution"] for j in jobs if j["release"]>=a and j["deadline"]<=b)
            excess=work-(b-a)
            if excess>0: excesses.append((excess,a,b,work))
    maximum=max((x[0] for x in excesses),default=0)
    witnesses=[{"start":a,"end":b,"demand":work,"capacity":b-a,"excess":ex}
               for ex,a,b,work in excesses if ex==maximum]
    return {"feasible":maximum==0,"max_excess":maximum,"witnesses":witnesses}

def exhaustive(jobs):
    if not jobs: return {"feasible":True,"schedule":[]}
    start=min(j["release"] for j in jobs); end=max(j["deadline"] for j in jobs)
    ids=tuple(j["id"] for j in jobs); ix={j:i for i,j in enumerate(ids)}
    releases=tuple(j["release"] for j in jobs); deadlines=tuple(j["deadline"] for j in jobs)
    initial=tuple(j["execution"] for j in jobs)
    @lru_cache(None)
    def visit(t,remaining):
        if t>=end: return () if not any(remaining) else None
        if any(remaining[i] and deadlines[i]<=t for i in range(len(ids))): return None
        ready=[i for i,r in enumerate(remaining) if r and releases[i]<=t]
        # Trying idle is unnecessary while a ready job exists for feasibility, but include it
        # so the recurrence remains a complete schedule search.
        for i in ready+[-1]:
            nxt=list(remaining)
            if i>=0: nxt[i]-=1
            suffix=visit(t+1,tuple(nxt))
            if suffix is not None: return ((t,ids[i] if i>=0 else None),)+suffix
        return None
    found=visit(start,initial)
    return {"feasible":found is not None,"schedule":[] if found is None else [{"tick":t,"job":j} for t,j in found]}

def bad_policy(jobs):
    """Preemptive but deliberately serves best-effort before control."""
    if not jobs: return {"misses":[],"schedule":[]}
    end=max(j["deadline"] for j in jobs); remaining={j["id"]:j["execution"] for j in jobs}
    schedule=[]; missed=set()
    for t in range(min(j["release"] for j in jobs),end):
        ready=[j for j in jobs if j["release"]<=t and remaining[j["id"]]>0]
        ready.sort(key=lambda j:(0 if j["class"]=="best_effort" else 1,j["deadline"],j["id"]))
        chosen=ready[0]["id"] if ready else None
        schedule.append({"tick":t,"job":chosen})
        if chosen is not None: remaining[chosen]-=1
        missed.update(j["id"] for j in jobs if j["deadline"]==t+1 and remaining[j["id"]]>0)
    misses=sorted(missed)
    return {"misses":misses,"schedule":schedule}

def classify(case):
    jobs=case.get("jobs")
    if not isinstance(jobs,list) or not jobs:
        return {"status":"HOLD_NO_SCHEDULABILITY_INPUTS"}
    for job in jobs:
        if any(k not in job for k in REQUIRED):
            return {"status":"HOLD_NO_SCHEDULABILITY_INPUTS"}
        if job["preemptible"] is not True:
            return {"status":"UNKNOWN_MODEL_MISMATCH"}
        if any(type(job[k]) is not int for k in ("release","execution","deadline")) or job["execution"]<=0 or job["release"]<0 or job["deadline"]<=job["release"]:
            return {"status":"HOLD_NO_SCHEDULABILITY_INPUTS"}
    controls=[j for j in jobs if j["class"]=="control"]
    all_demand=demand(jobs); control_demand=demand(controls)
    all_sched=exhaustive(jobs); control_sched=exhaustive(controls); policy=bad_policy(jobs)
    return {"status":"ELIGIBLE","control_demand":control_demand,"all_demand":all_demand,
            "control_exhaustive":control_sched,"all_exhaustive":all_sched,"bad_policy":policy,
            "diagnosis":"POLICY_MISS_ON_FEASIBLE_TRACE" if all_sched["feasible"] and policy["misses"] else
                       ("JOINT_DEMAND_INFEASIBLE" if control_sched["feasible"] and not all_sched["feasible"] else
                        ("CONTROL_DEMAND_INFEASIBLE" if not control_sched["feasible"] else "FEASIBLE_NO_POLICY_MISS"))}

def build(cases):
    rows=[]
    for case in cases["cases"]:
        rows.append({"input":case,"result":classify(case)})
    return {"schema":"7748-demand-witness-t0-v1","model":cases["model"],"rows":rows}

if __name__=="__main__": json.dump(build(json.load(open(sys.argv[1],encoding="utf-8"))),sys.stdout,sort_keys=True,separators=(",",":"))
