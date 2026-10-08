"""Independent finite trace adjudicator; deliberately does not import candidate."""
from functools import lru_cache

FIELDS=("id","class","release","execution","deadline","preemptible")

def _interval_oracle(work):
    endpoints=sorted({j["release"] for j in work}|{j["deadline"] for j in work})
    worst=0; witnesses=[]
    for left in endpoints:
        for right in endpoints:
            if right<=left: continue
            required=sum(j["execution"] for j in work if left<=j["release"] and j["deadline"]<=right)
            surplus=required-(right-left)
            if surplus>worst:
                worst=surplus; witnesses=[[left,right,required,right-left,surplus]]
            elif surplus>0 and surplus==worst:
                witnesses.append([left,right,required,right-left,surplus])
    return {"feasible":worst==0,"max_excess":worst,
            "witnesses":[{"start":a,"end":b,"demand":d,"capacity":c,"excess":x}
                         for a,b,d,c,x in witnesses]}

def _slot_oracle(work):
    if not work: return {"feasible":True,"schedule":[]}
    lo=min(j["release"] for j in work); hi=max(j["deadline"] for j in work)
    jobs=tuple(work); remaining=tuple(j["execution"] for j in jobs)
    states={remaining:[]}
    for now in range(lo,hi):
        after={}
        for rem,prefix in states.items():
            if any(rem[i] and jobs[i]["deadline"]<=now for i in range(len(jobs))): continue
            choices=[i for i,j in enumerate(jobs) if rem[i] and j["release"]<=now]
            for picked in choices+[-1]:
                nxt=list(rem)
                row={"tick":now,"job":None}
                if picked>=0:
                    nxt[picked]-=1; row["job"]=jobs[picked]["id"]
                tup=tuple(nxt)
                after.setdefault(tup,prefix+[row])
        states=after
    for rem,prefix in states.items():
        if not any(rem): return {"feasible":True,"schedule":prefix}
    return {"feasible":False,"schedule":[]}

def _priority_trace(work):
    if not work: return {"misses":[],"schedule":[]}
    pending={j["id"]:j["execution"] for j in work}; schedule=[]; late=set()
    for now in range(min(j["release"] for j in work),max(j["deadline"] for j in work)):
        eligible=[j for j in work if j["release"]<=now and pending[j["id"]]>0]
        chosen=min(eligible,key=lambda j:(j["class"]!="best_effort",j["deadline"],j["id"])) if eligible else None
        schedule.append({"tick":now,"job":None if chosen is None else chosen["id"]})
        if chosen is not None: pending[chosen["id"]]-=1
        late.update(j["id"] for j in work if j["deadline"]==now+1 and pending[j["id"]]>0)
    return {"misses":sorted(late),"schedule":schedule}

def _classify(case):
    jobs=case.get("jobs")
    if not isinstance(jobs,list) or not jobs: return {"status":"HOLD_NO_SCHEDULABILITY_INPUTS"}
    for j in jobs:
        if any(f not in j for f in FIELDS): return {"status":"HOLD_NO_SCHEDULABILITY_INPUTS"}
        if j["preemptible"] is not True: return {"status":"UNKNOWN_MODEL_MISMATCH"}
        if any(type(j[k]) is not int for k in ("release","execution","deadline")) or j["release"]<0 or j["execution"]<=0 or j["deadline"]<=j["release"]:
            return {"status":"HOLD_NO_SCHEDULABILITY_INPUTS"}
    control=[j for j in jobs if j["class"]=="control"]
    da,dc=_interval_oracle(jobs),_interval_oracle(control)
    ea,ec=_slot_oracle(jobs),_slot_oracle(control)
    pol=_priority_trace(jobs)
    diagnosis=("POLICY_MISS_ON_FEASIBLE_TRACE" if ea["feasible"] and pol["misses"] else
               "JOINT_DEMAND_INFEASIBLE" if ec["feasible"] and not ea["feasible"] else
               "CONTROL_DEMAND_INFEASIBLE" if not ec["feasible"] else "FEASIBLE_NO_POLICY_MISS")
    return {"status":"ELIGIBLE","control_demand":dc,"all_demand":da,
            "control_exhaustive":ec,"all_exhaustive":ea,"bad_policy":pol,"diagnosis":diagnosis}

def audit(raw,frozen):
    errors=[]
    if raw.get("schema")!="7748-demand-witness-t0-v1": errors.append("schema")
    if raw.get("model")!=frozen.get("model"): errors.append("model_mismatch")
    expected=frozen.get("cases",[])
    rows=raw.get("rows",[])
    if len(rows)!=len(expected): errors.append("case_count")
    by_id={r.get("input",{}).get("id"):r for r in rows}
    if len(by_id)!=len(rows): errors.append("duplicate_or_missing_id")
    for case in expected:
        row=by_id.get(case["id"])
        if row is None: errors.append("missing:"+case["id"]); continue
        if row.get("input")!=case: errors.append("input_mutation:"+case["id"])
        replay=_classify(case)
        if row.get("result")!=replay: errors.append("result_mismatch:"+case["id"])
        if replay.get("status")=="ELIGIBLE":
            if replay["all_demand"]["feasible"]!=replay["all_exhaustive"]["feasible"]:
                errors.append("oracle_disagreement:"+case["id"])
            if replay["control_demand"]["feasible"]!=replay["control_exhaustive"]["feasible"]:
                errors.append("control_oracle_disagreement:"+case["id"])
    return {"status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD","errors":errors,"cases":len(expected)}

if __name__=="__main__":
    import json,sys
    print(json.dumps(audit(json.load(open(sys.argv[1],encoding="utf-8")),json.load(open(sys.argv[2],encoding="utf-8"))),sort_keys=True))
