"""Independent replay from hidden fixture construction; does not import runner."""
import hashlib,json,math,random
from pathlib import Path
ROOT=Path(__file__).parent
P=json.loads((ROOT/"protocol.json").read_text())


def plant(seed,condition):
    r=random.Random(seed*117+len(condition)*7919)
    if condition=="constant": return [[1.0,0.0],[0.0,1.0]]
    if condition=="gain_drift": return [[r.uniform(.58,1.52),0.0],[0.0,r.uniform(.58,1.52)]]
    a,b=r.uniform(.72,1.28),r.uniform(.72,1.28)
    c,d=r.uniform(-.30,.30),r.uniform(-.30,.30)
    if condition=="cross_coupling": c,d=r.uniform(-.38,.38),r.uniform(-.38,.38)
    return [[a,c],[d,b]]


def audit(rows):
    errors=[]; lo,hi=P["heldout_seeds"]; conditions=P["conditions"]; arms=P["arms"]
    expected={(c,s,a) for c in conditions for s in range(lo,hi+1) for a in arms}
    keys=[(r.get("condition"),r.get("seed"),r.get("arm")) for r in rows]
    if set(keys)!=expected or len(keys)!=len(expected): errors.append("PAIR_GRID_INCOMPLETE_OR_DUPLICATE")
    by={}
    for r in rows:
        c,s,a=r["condition"],r["seed"],r["arm"]; by[(c,s,a)]=r
        m=plant(s,c); state=[0.0,0.0]; start=r["start_error"]
        for i,u in enumerate(r["actions"]):
            if math.hypot(*u)>P["max_action_norm"]+1e-9: errors.append(f"ACTION_BOUND:{c}:{s}:{a}:{i}")
            delta=[sum(m[k][j]*u[j] for j in range(2)) for k in range(2)]
            if c=="saturation": delta=[max(-5.0,min(5.0,x)) for x in delta]
            state=[state[k]+delta[k] for k in range(2)]
            after=[start[k]-state[k] for k in range(2)]
            try:
                ev=r["candidate"]["rows"][i]
                if ev["before"] != (start if i==0 else r["candidate"]["rows"][i-1]["after"]) or ev["after"]!=after or ev["action"]!=u:
                    errors.append(f"TRACE:{c}:{s}:{a}:{i}")
            except (IndexError,KeyError): errors.append(f"MISSING_EVENT:{c}:{s}:{a}:{i}")
        terminal=math.hypot(start[0]-state[0],start[1]-state[1])
        if abs(terminal-r["terminal_error"])>1e-9: errors.append(f"TERMINAL:{c}:{s}:{a}")
        if (terminal<=P["target_tolerance_pixels"])!=r["goal_reached"]: errors.append(f"ORACLE:{c}:{s}:{a}")
        if r["safety_violation"]: errors.append(f"SAFETY:{c}:{s}:{a}")
        if len(r["actions"])!=r["candidate"]["corrections"]: errors.append(f"COUNT:{c}:{s}:{a}")
    totals={}
    for c in conditions:
        pairs=[]
        for s in range(lo,hi+1):
            f=by[(c,s,"fixed_gain")]; j=by[(c,s,"online_jacobian")]
            if f["goal_reached"]!=j["goal_reached"]: errors.append(f"GOAL_NONMATCH:{c}:{s}")
            pairs.append((f["candidate"]["corrections"],j["candidate"]["corrections"]))
        totals[c]={"fixed":sum(x for x,_ in pairs),"online_jacobian":sum(y for _,y in pairs)}
    subset=[(x,y) for c in P["adaptation_subset"] for s in range(lo,hi+1)
            for x,y in [(by[(c,s,"fixed_gain")]["candidate"]["corrections"],by[(c,s,"online_jacobian")]["candidate"]["corrections"])]]
    fixed=sum(x for x,_ in subset); online=sum(y for _,y in subset)
    reduction=1-online/fixed if fixed else 0.0
    reached=all(r["goal_reached"] for r in rows)
    status="PASS_METHOD_SCOPED" if not errors and reached and reduction>=P["required_improvement_fraction"] else "FAIL_NO_GAIN" if not errors else "HOLD_AUDIT_OR_OUTCOME"
    return {"status":status,"errors":errors,"rows":len(rows),"all_goals_reached":reached,
        "adaptation_subset_fixed":fixed,"adaptation_subset_online":online,
        "correction_reduction_fraction":reduction,"per_condition_totals":totals,
        "safety_violations":sum(bool(r["safety_violation"]) for r in rows)}


def main():
    path=ROOT/"formal_01/RAW.jsonl"; rows=[json.loads(x) for x in path.read_text().splitlines()]
    result=audit(rows); result["raw_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT/"formal_01/AUDIT.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if result["status"]!="PASS_METHOD_SCOPED": raise SystemExit(1)


if __name__=="__main__": main()
