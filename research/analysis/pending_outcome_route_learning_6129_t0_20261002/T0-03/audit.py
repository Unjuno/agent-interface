import json,sys
from fractions import Fraction

IDS={"delay_inversion","equal_delay_null","known_independent_loss","typed_terminals","yield_recovery","unknown_loss","state_coupled"}

def rate(rows): return Fraction(sum(x[1]=="VERIFIED_SUCCESS" for x in rows),len(rows))

def audit(v,t,out):
    err=[]; cases={x["id"]:x for x in v["cases"]}; got=out.get("cases",{})
    if set(cases)!=IDS or set(got)!=IDS:err.append("case_set")
    for cid in sorted(IDS & set(cases) & set(got)):
        c=cases[cid]; result=got[cid]; exp=t["expected_as_of"][cid]
        if result.get("pending_aware")!=exp["pending_aware"]:err.append(cid+":pending_decision")
        if "complete_case" in exp and result.get("complete_case")!=exp["complete_case"]:err.append(cid+":complete_case_decision")
        groups={}
        for a in c["attempts"]:groups.setdefault(a["route"],[]).append(a)
        for route,rows in ({} if cid=="state_coupled" else groups).items():
            states=[x["as_of"] for x in rows]; counts=result.get("routes",{}).get(route,{}).get("counts",{})
            if any(counts.get(s,0)!=states.count(s) for s in set(states)):err.append(cid+":counts:"+route)
            complete=[s for s in states if s in {"VERIFIED_SUCCESS","VERIFIED_FAILURE","VERIFIED_WRONG_EFFECT"}]
            cr=str(Fraction(sum(s=="VERIFIED_SUCCESS" for s in complete),len(complete))) if complete else None
            lo=str(Fraction(states.count("VERIFIED_SUCCESS"),len(states)))
            hi=str(Fraction(states.count("VERIFIED_SUCCESS")+sum(states.count(x) for x in ["PENDING","YIELD","ADMIN_LOST_FOLLOWUP"]),len(states)))
            r=result.get("routes",{}).get(route,{})
            if r.get("complete_case_rate")!=cr or r.get("bounds")!=[lo,hi]:err.append(cid+":rate_bounds:"+route)
    # Independently rebuild the frozen terminal/delay table, not just candidate labels.
    rows=t["terminal_events"]["delay_inversion"]
    attempts={x["id"]:x for x in cases["delay_inversion"]["attempts"]}
    if {r[0] for r in rows}!=set(attempts):err.append("terminal_attempt_set")
    times={r[0]:r[2] for r in rows}
    if any((attempts[i]["as_of"]=="PENDING")!=(times[i]>v["as_of"]) for i in attempts):err.append("as_of_future_consistency")
    routes={"A":[],"B":[]}
    for aid,status,tick in rows: routes[attempts[aid]["route"]].append((aid,status,tick))
    complete={r:Fraction(sum(z[1]=="VERIFIED_SUCCESS" for z in vals if z[2]<=v["as_of"]),sum(z[2]<=v["as_of"] for z in vals)) for r,vals in routes.items()}
    final={r:rate(vals) for r,vals in routes.items()}
    if complete!={"A":Fraction(0),"B":Fraction(1,2)}:err.append("complete_case_inversion_reconstruction")
    if {r:str(x) for r,x in final.items()}!=t["expected_deadline_success_rates"]["delay_inversion"]:err.append("deadline_rates")
    # Switching-cost reconstruction and policy total-work ledger.
    unit=sum(v["switch_cost"].values())
    if unit!=t["switch_per_change"] or out.get("switching",{}).get("per_change")!=unit:err.append("switch_unit")
    for name,path in v["policy_paths"].items():
        changes=sum(a!=b for a,b in zip(path["routes"],path["routes"][1:])); item=out.get("switching",{}).get("policies",{}).get(name,{})
        if item.get("changes")!=changes or item.get("switch_cost")!=changes*unit or item.get("total_work")!=path["base_work"]+changes*unit:err.append("switch_total:"+name)
    return {"status":"PASS_METHOD_SCOPED" if not err else "FAIL","reconstructed_cases":len(set(cases)&IDS),"complete_case_rates":{r:str(x) for r,x in complete.items()},"deadline_rates":{r:str(x) for r,x in final.items()},"errors":err}

def main(vp,tp,op,dp):
    v=json.load(open(vp));t=json.load(open(tp));o=json.load(open(op));res=audit(v,t,o)
    with open(dp,"w") as f:json.dump(res,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(res,sort_keys=True));return 0 if not res["errors"] else 1
if __name__=="__main__":raise SystemExit(main(*sys.argv[1:5]))
