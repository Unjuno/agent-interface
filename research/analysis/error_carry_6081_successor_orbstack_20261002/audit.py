import json, sys
from fractions import Fraction as Q
from pathlib import Path

POLICIES=("A_HORIZON_NEAREST","B_SLOT_NEAREST","C_ERROR_CARRY","D_RELEASE")

def valid(v, alphabet):
    x,y=v
    return abs(x)+abs(y)<=1 if alphabet=="4way" else max(abs(x),abs(y))<=1

def reference(case, vectors, policy):
    target=tuple(Q(s) for s in case["intent"]); horizon=case["horizon"]
    if case.get("control")=="unknown_calibration":
        return {"status":"REFUSE_UNKNOWN_CALIBRATION","moves":[],"positions":[],"release":True,"switches":0}
    if not valid(target,case["action_set"]):
        return {"status":"REFUSE_OUTSIDE_HULL","moves":[],"positions":[],"release":True,"switches":0}
    if policy=="D_RELEASE": seq=[(Q(0),Q(0)) for _ in range(horizon)]
    elif policy in POLICIES[:2]:
        # Independent exhaustive argmin, with the declared alphabet order as tie break.
        costs=[( (v[0]-target[0])**2+(v[1]-target[1])**2, i, v) for i,v in enumerate(vectors) ]
        action=min(costs)[2]; seq=[action for _ in range(horizon)]
    else:
        seq=[]; x=Q(0); y=Q(0)
        for t in range(1,horizon+1):
            options=[]
            for j,v in enumerate(vectors):
                dx=t*target[0]-x-v[0]; dy=t*target[1]-y-v[1]
                options.append((dx*dx+dy*dy,j,v))
            action=min(options)[2]; seq.append(action); x+=action[0]; y+=action[1]
    x=Q(0); y=Q(0); trail=[]; errs=[]; breaches=0
    xl,xh,yl,yh=(Q(t) for t in case["box"])
    for t,(dx,dy) in enumerate(seq,1):
        x+=dx; y+=dy; trail.append([str(x),str(y)])
        ex=x-t*target[0]; ey=y-t*target[1]; errs.append(str(ex*ex+ey*ey))
        breaches+=int(not(xl<=x<=xh and yl<=y<=yh))
    changes=sum(seq[j]!=seq[j-1] for j in range(1,len(seq)))
    state="UNSAFE_PREFIX" if breaches else "SCHEDULED"
    if changes>case["max_switches"]: state="SWITCH_LIMIT_EXCEEDED"
    return {"status":state,"moves":[[str(q) for q in v] for v in seq],"positions":trail,
            "prefix_error_sq":errs,"terminal_error_sq":errs[-1] if errs else "0",
            "envelope_violations":breaches,"switches":changes,"release":True}

def main(fixture,raw,out):
    spec=json.loads(Path(fixture).read_text()); observed=json.loads(Path(raw).read_text())
    expected=[]
    for label, entries in spec["action_sets"].items():
        vectors=[tuple(Q(x) for x in pair) for pair in entries]
        for case in spec["cases"]:
            c=dict(case,action_set=label)
            for p in POLICIES:
                expected.append({"action_set":label,"case":case["id"],"policy":p,
                                 "result":reference(c,vectors,p)})
    if observed.get("schema")!="error-carry-raw-v1" or observed.get("rows")!=expected:
        raise SystemExit("FAIL_RAW_RECONSTRUCTION")
    indexed={(r["action_set"],r["case"],r["policy"]):r["result"] for r in expected}
    eligible=[]; wins=[]; unsafe=[]; duplicate=[]
    for label in spec["action_sets"]:
        for c in spec["cases"]:
            key=(label,c["id"]); a=indexed[(label,c["id"],POLICIES[0])]; b=indexed[(label,c["id"],POLICIES[1])]; carry=indexed[(label,c["id"],POLICIES[2])]
            if a!=b: raise SystemExit("FAIL_STATIONARY_BASELINE_EQUIVALENCE")
            duplicate.append(key)
            if c.get("control") or c["id"] in ("exact-east","zero"): continue
            if carry["status"]=="SCHEDULED" and a["status"]=="SCHEDULED":
                eligible.append(key)
                aw=max(Q(e) for e in a["prefix_error_sq"]); cw=max(Q(e) for e in carry["prefix_error_sq"])
                if cw<aw: wins.append(key)
            if carry["envelope_violations"]: unsafe.append((key,"C"))
    result={"status":"PASS_METHOD_SCOPED" if len(wins)>=3 and not unsafe else "FAIL_METHOD_OR_SAFETY_GATE",
            "rows_reconstructed":len(expected),"a_b_equivalence_cases":len(duplicate),
            "eligible_cases":len(eligible),"error_carry_wins":len(wins),
            "win_cases":[list(x) for x in wins],"unsafe_carry_cases":[[list(k),p] for k,p in unsafe],
            "scope":"exact rational constant-displacement synthetic fixture only"}
    Path(out).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    if result["status"]!="PASS_METHOD_SCOPED": raise SystemExit(result["status"])
if __name__=="__main__": main(sys.argv[1],sys.argv[2],sys.argv[3])
