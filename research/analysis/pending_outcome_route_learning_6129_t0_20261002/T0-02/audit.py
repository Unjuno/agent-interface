import json
import sys
from fractions import Fraction

EXPECTED={"delay_inversion","equal_delay_null","known_noninformative_admin_loss","typed_safe_stop_vs_wrong_effect","yield_then_recovered_success","unknown_outcome_dependent_loss","state_coupled_cross_task"}

def audit(visible,truth,result):
    errors=[]; cases={c["id"]:c for c in visible["cases"]}; got=result.get("cases",{})
    if set(cases)!=EXPECTED or set(got)!=EXPECTED: errors.append("case_set")
    for cid in sorted(EXPECTED & set(cases) & set(got)):
        case=cases[cid]; route_rows={}
        for row in case["attempts"]: route_rows.setdefault(row["route"],[]).append(row)
        entry=got[cid]
        if entry.get("decision")!=truth["expected"][cid]: errors.append(cid+":decision")
        if cid not in {"unknown_outcome_dependent_loss","state_coupled_cross_task"}:
            for route,rows in route_rows.items():
                tally={k:0 for k in ["VERIFIED_SUCCESS","VERIFIED_FAILURE","VERIFIED_WRONG_EFFECT","POLICY_TERMINAL_SAFE_STOP","ADMIN_LOST_FOLLOWUP","PENDING","YIELD"]}
                for row in rows:
                    types=[e["type"] for e in row["events"] if e["t"]<=visible["as_of"]]
                    last=types[-1]
                    if last=="YIELD": tally["YIELD"]+=1; tally["PENDING"]+=1
                    elif last in tally: tally[last]+=1
                    else: tally["PENDING"]+=1
                expected_bound=[str(Fraction(tally["VERIFIED_SUCCESS"],len(rows))),str(Fraction(tally["VERIFIED_SUCCESS"]+tally["PENDING"]+tally["ADMIN_LOST_FOLLOWUP"],len(rows)))]
                actual=entry.get("routes",{}).get(route,{})
                if actual.get("counts")!=tally or actual.get("success_bounds")!=expected_bound: errors.append(cid+":count_or_bound:"+route)
        if cid=="yield_then_recovered_success" and (entry["routes"]["RECOVER"]["counts"]["YIELD"]!=1 or entry["routes"]["RECOVER"]["counts"]["VERIFIED_SUCCESS"]!=0): errors.append("yield_collapsed_or_lookahead")
        if cid=="typed_safe_stop_vs_wrong_effect":
            if entry["routes"]["SAFE"]["counts"]["POLICY_TERMINAL_SAFE_STOP"]!=1 or entry["routes"]["WRONG"]["counts"]["VERIFIED_WRONG_EFFECT"]!=1: errors.append("typed_terminal_collapse")
    components=visible["switch_cost"]; per=sum(components.values())
    if result.get("switch_cost",{}).get("per_switch")!=per: errors.append("switch_component_sum")
    for name,path in visible["policy_paths"].items():
        switches=sum(a!=b for a,b in zip(path["routes"],path["routes"][1:])); row=result.get("switch_cost",{}).get("policies",{}).get(name,{})
        if row.get("switches")!=switches or row.get("switch_work_units")!=switches*per or row.get("total_work_units")!=path["base_work_units"]+switches*per: errors.append("switch_accounting:"+name)
    return {"status":"PASS_METHOD_SCOPED" if not errors else "FAIL","reconstructed_cases":len(set(cases)&EXPECTED),"errors":errors}

def main(vp,tp,rp,op):
    v=json.load(open(vp)); t=json.load(open(tp)); r=json.load(open(rp)); out=audit(v,t,r)
    with open(op,"w") as f: json.dump(out,f,indent=2,sort_keys=True); f.write("\n")
    print(json.dumps(out,sort_keys=True)); return 0 if not out["errors"] else 1
if __name__=="__main__": raise SystemExit(main(*sys.argv[1:5]))
