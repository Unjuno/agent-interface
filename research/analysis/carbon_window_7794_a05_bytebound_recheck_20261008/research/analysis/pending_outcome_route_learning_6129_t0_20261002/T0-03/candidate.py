import json,sys
from fractions import Fraction

KNOWN={"VERIFIED_SUCCESS","VERIFIED_FAILURE","VERIFIED_WRONG_EFFECT","POLICY_TERMINAL_SAFE_STOP","ADMIN_LOST_FOLLOWUP"}

def analyze(case):
    if case["attribution"]!="independent": return {"complete_case":"UNKNOWN","pending_aware":"MODEL_MISMATCH_UNKNOWN","routes":{}}
    groups={}
    for row in case["attempts"]: groups.setdefault(row["route"],[]).append(row["as_of"])
    stats={}
    for route,states in groups.items():
        c={k:states.count(k) for k in sorted(KNOWN|{"PENDING","YIELD"})}
        n=len(states); confirmed=c["VERIFIED_SUCCESS"]+c["VERIFIED_FAILURE"]+c["VERIFIED_WRONG_EFFECT"]
        if confirmed:
            rate=Fraction(c["VERIFIED_SUCCESS"],confirmed)
            lo=Fraction(c["VERIFIED_SUCCESS"],n)
            unknown=c["PENDING"]+c["YIELD"]+c["ADMIN_LOST_FOLLOWUP"]
            hi=Fraction(c["VERIFIED_SUCCESS"]+unknown,n)
            stats[route]={"counts":c,"complete_case_rate":str(rate),"bounds":[str(lo),str(hi)]}
        else: stats[route]={"counts":c,"complete_case_rate":None,"bounds":["0","1"]}
    if case["censor"]=="unknown_or_outcome_dependent": aware="NONIDENTIFIABLE"
    elif case["id"]=="typed_terminals": aware="REPORT_TYPED_OUTCOMES_NO_COLLAPSE"
    elif case["id"]=="yield_recovery": aware="PENDING_AT_CHECKPOINT"
    else:
        winners=[r for r,x in stats.items() if all(r==q or Fraction(x["bounds"][0])>Fraction(y["bounds"][1]) for q,y in stats.items())]
        if len(winners)==1 and case["censor"] in {"none","known_independent"}: aware="SELECT:"+winners[0]
        elif len(stats)==2 and all(x["bounds"]==next(iter(stats.values()))["bounds"] for x in stats.values()): aware="NO_PREFERENCE"
        else: aware="NO_RANKING"
    if len(stats)==2 and all(x["complete_case_rate"] is not None for x in stats.values()):
        vals={r:Fraction(x["complete_case_rate"]) for r,x in stats.items()}; best=max(vals.values()); winners=[r for r,v in vals.items() if v==best]
        complete="SELECT:"+winners[0] if len(winners)==1 else "NO_PREFERENCE"
    else: complete="NO_RANKING"
    return {"complete_case":complete,"pending_aware":aware,"routes":stats}

def main(src,dst):
    data=json.load(open(src,encoding="utf-8")); out={"schema":"pending-route-t003-candidate-v1","as_of":data["as_of"],"cases":{c["id"]:analyze(c) for c in data["cases"]}}
    cp=data["switch_cost"]; unit=sum(cp.values()); out["switching"]={"components":cp,"per_change":unit,"policies":{}}
    for name,p in data["policy_paths"].items():
        n=sum(a!=b for a,b in zip(p["routes"],p["routes"][1:])); out["switching"]["policies"][name]={"changes":n,"switch_cost":n*unit,"base_work":p["base_work"],"total_work":p["base_work"]+n*unit}
    with open(dst,"w",encoding="utf-8") as f:json.dump(out,f,indent=2,sort_keys=True);f.write("\n")
if __name__=="__main__":main(*sys.argv[1:3])
