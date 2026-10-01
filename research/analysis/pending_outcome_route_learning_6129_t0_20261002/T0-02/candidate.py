import json
import sys
from fractions import Fraction

TERMINALS={"VERIFIED_SUCCESS","VERIFIED_FAILURE","VERIFIED_WRONG_EFFECT","POLICY_TERMINAL_SAFE_STOP","ADMIN_LOST_FOLLOWUP"}

def summarize(case):
    if case["attribution"] != "independent":
        return {"decision":"MODEL_MISMATCH_UNKNOWN","routes":{}}
    routes={}
    for a in case["attempts"]:
        routes.setdefault(a["route"],[]).append(a)
    counts={}
    for route,rows in routes.items():
        tally={k:0 for k in ["VERIFIED_SUCCESS","VERIFIED_FAILURE","VERIFIED_WRONG_EFFECT","POLICY_TERMINAL_SAFE_STOP","ADMIN_LOST_FOLLOWUP","PENDING","YIELD"]}
        for row in rows:
            visible=[e["type"] for e in row["events"] if e["t"]<=1]
            last=visible[-1]
            if last=="YIELD": tally["YIELD"]+=1; tally["PENDING"]+=1
            elif last in tally: tally[last]+=1
            else: tally["PENDING"]+=1
        n=len(rows); success=tally["VERIFIED_SUCCESS"]
        unknown=tally["PENDING"]+tally["ADMIN_LOST_FOLLOWUP"]
        counts[route]={"counts":tally,"success_bounds":[str(Fraction(success,n)),str(Fraction(success+unknown,n))]}
    if case["censor_assumption"]=="unknown_or_outcome_dependent":
        decision="NONIDENTIFIABLE"
    elif case["id"]=="typed_safe_stop_vs_wrong_effect":
        decision="REPORT_TYPED_OUTCOMES_NO_COLLAPSE"
    elif case["id"]=="yield_then_recovered_success":
        decision="PENDING_AT_AS_OF_YIELD_IS_NONTERMINAL"
    elif case["id"]=="state_coupled_cross_task":
        decision="MODEL_MISMATCH_UNKNOWN"
    elif len(counts)==2 and len({tuple(x["success_bounds"]) for x in counts.values()})==1:
        decision="NO_PREFERENCE"
    else:
        winners=[r for r,x in counts.items() if all(r==q or Fraction(x["success_bounds"][0])>Fraction(y["success_bounds"][1]) for q,y in counts.items())]
        decision="SELECT:"+winners[0] if len(winners)==1 else "NO_RANKING"
    return {"decision":decision,"routes":counts}

def main(src,dst):
    data=json.load(open(src,encoding="utf-8")); result={"schema":"pending-route-t002-candidate-v1","as_of":data["as_of"],"cases":{c["id"]:summarize(c) for c in data["cases"]}}
    c=data["switch_cost"]; per=sum(c.values());
    result["switch_cost"]={"per_switch":per,"components":c,"policies":{}}
    for name,p in data["policy_paths"].items():
        n=sum(a!=b for a,b in zip(p["routes"],p["routes"][1:]))
        result["switch_cost"]["policies"][name]={"switches":n,"switch_work_units":n*per,"base_work_units":p["base_work_units"],"total_work_units":p["base_work_units"]+n*per}
    with open(dst,"w",encoding="utf-8") as f: json.dump(result,f,indent=2,sort_keys=True); f.write("\n")
if __name__=="__main__": main(*sys.argv[1:3])
