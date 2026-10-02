import json, sys
from fractions import Fraction as F
from pathlib import Path

def inside_hull(v, name):
    x,y=v
    if name=="4way": return abs(x)+abs(y)<=1
    return max(abs(x),abs(y))<=1

def simulate(case, actions, policy):
    n=case["horizon"]; v=tuple(F(x) for x in case["intent"])
    if case.get("control")=="unknown_calibration":
        return {"status":"REFUSE_UNKNOWN_CALIBRATION","moves":[],"positions":[],"release":True,"switches":0}
    if not inside_hull(v, case["action_set"]):
        return {"status":"REFUSE_OUTSIDE_HULL","moves":[],"positions":[],"release":True,"switches":0}
    if policy=="D_RELEASE": moves=[(0,0)]*n
    elif policy in ("A_HORIZON_NEAREST","B_SLOT_NEAREST"):
        # Both minimize exact squared Euclidean displacement error. With stationary
        # actions and constant intent, the minimizing action is identical each slot.
        a=min(actions,key=lambda q: ((q[0]-v[0])**2+(q[1]-v[1])**2, actions.index(q)))
        moves=[a]*n
    elif policy=="C_ERROR_CARRY":
        moves=[]; pos=[F(0),F(0)]
        for k in range(1,n+1):
            target=[k*v[0],k*v[1]]
            a=min(actions,key=lambda q: ((target[0]-pos[0]-q[0])**2+(target[1]-pos[1]-q[1])**2, actions.index(q)))
            moves.append(a); pos=[pos[0]+a[0],pos[1]+a[1]]
    else: raise ValueError(policy)
    pos=[F(0),F(0)]; positions=[]; errors=[]; violations=0
    xmin,xmax,ymin,ymax=map(F,case["box"])
    for k,a in enumerate(moves,1):
        pos=[pos[0]+a[0],pos[1]+a[1]]; positions.append([str(z) for z in pos])
        target=[k*v[0],k*v[1]]
        errors.append(str((pos[0]-target[0])**2+(pos[1]-target[1])**2))
        violations += int(not(xmin<=pos[0]<=xmax and ymin<=pos[1]<=ymax))
    switches=sum(moves[i]!=moves[i-1] for i in range(1,len(moves)))
    status="UNSAFE_PREFIX" if violations else "SCHEDULED"
    if switches>case["max_switches"]: status="SWITCH_LIMIT_EXCEEDED"
    return {"status":status,"moves":[[str(z) for z in a] for a in moves],"positions":positions,
            "prefix_error_sq":errors,"terminal_error_sq":errors[-1] if errors else "0",
            "envelope_violations":violations,"switches":switches,"release":True}

def main(src,out):
    data=json.loads(Path(src).read_text()); rows=[]
    policies=["A_HORIZON_NEAREST","B_SLOT_NEAREST","C_ERROR_CARRY","D_RELEASE"]
    for name,raw_actions in data["action_sets"].items():
        actions=[tuple(map(F,a)) for a in raw_actions]
        for c in data["cases"]:
            case=dict(c,action_set=name)
            for policy in policies:
                rows.append({"action_set":name,"case":c["id"],"policy":policy,
                             "result":simulate(case,actions,policy)})
    Path(out).write_text(json.dumps({"schema":"error-carry-raw-v1","rows":rows},sort_keys=True,separators=(",",":"))+"\n")
if __name__=="__main__": main(sys.argv[1],sys.argv[2])
