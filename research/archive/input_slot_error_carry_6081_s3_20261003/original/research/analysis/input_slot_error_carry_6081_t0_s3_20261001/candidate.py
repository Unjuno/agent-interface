"""Offline exact-grid input-slot compiler candidate for Issue #6081 T0."""
import argparse
import json
from fractions import Fraction
from pathlib import Path


def frac(x):
    return Fraction(x)


def cross(a, b, p):
    return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])


def hull(points):
    pts=sorted(set(points))
    if len(pts)<=1:return pts
    lo=[]
    for p in pts:
        while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    hi=[]
    for p in reversed(pts):
        while len(hi)>=2 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]


def in_hull(point, points):
    h=hull(points)
    if len(h)==1:return point==h[0]
    if len(h)==2:
        return cross(h[0],h[1],point)==0 and min(h[0][0],h[1][0])<=point[0]<=max(h[0][0],h[1][0]) and min(h[0][1],h[1][1])<=point[1]<=max(h[0][1],h[1][1])
    signs=[cross(h[i],h[(i+1)%len(h)],point) for i in range(len(h))]
    return all(v>=0 for v in signs) or all(v<=0 for v in signs)


def sumset(actions, horizon):
    states={(0,0)}
    for _ in range(horizon):
        states={(x+a[1],y+a[2]) for x,y in states for a in actions}
    return states


def sq(v):return v[0]*v[0]+v[1]*v[1]


def nearest(vector, actions):
    return min(actions,key=lambda a:sq((vector[0]-a[1],vector[1]-a[2])))


def switches(seq):return sum(a[0]!=b[0] for a,b in zip(seq,seq[1:]))


def carry(intents, actions, max_switches):
    seq=[]; error=(Fraction(0),Fraction(0)); change_count=0
    for intent in intents:
        eligible=actions
        if seq and change_count>=max_switches:
            eligible=[a for a in actions if a[0]==seq[-1][0]]
        action=min(eligible,key=lambda a:sq((error[0]+intent[0]-a[1],error[1]+intent[1]-a[2])))
        if seq and action[0]!=seq[-1][0]:change_count+=1
        seq.append(action);error=(error[0]+intent[0]-action[1],error[1]+intent[1]-action[2])
    return seq


def metrics(intents, seq, release_tick):
    target=(Fraction(0),Fraction(0)); actual=(Fraction(0),Fraction(0)); errors=[]
    for intent,action in zip(intents,seq):
        target=(target[0]+intent[0],target[1]+intent[1]);actual=(actual[0]+action[1],actual[1]+action[2])
        errors.append(sq((target[0]-actual[0],target[1]-actual[1])))
    return {"actions":[a[0] for a in seq],"switches":switches(seq),"prefix_error_sq":[str(x) for x in errors],"worst_prefix_error_sq":str(max(errors,default=Fraction(0))),"terminal_error_sq":str(errors[-1] if errors else Fraction(0)),"release_tick":release_tick,"released":True}


def compile_case(case, dictionaries):
    n=len(case["intents"])
    if not case.get("calibration_valid",False):return {"id":case["id"],"disposition":"REFUSE_CALIBRATION_MISMATCH","reachability":"NOT_EVALUATED","policies":{}}
    if case.get("dynamics")!="constant_linear":return {"id":case["id"],"disposition":"REFUSE_MODEL_MISMATCH","reachability":"NOT_EVALUATED","policies":{}}
    if not case.get("release_permitted",False):return {"id":case["id"],"disposition":"REFUSE_NO_RELEASE_PATH","reachability":"NOT_EVALUATED","policies":{}}
    if case.get("release_deadline",-1)<n:return {"id":case["id"],"disposition":"REFUSE_RELEASE_DEADLINE","reachability":"NOT_EVALUATED","policies":{}}
    actions=dictionaries[case["dictionary"]]["actions"]
    intents=[(frac(x),frac(y)) for x,y in case["intents"]]
    pts=[(a[1],a[2]) for a in actions]
    if any(not in_hull(v,pts) for v in intents):return {"id":case["id"],"disposition":"REFUSE_UNREPRESENTABLE","reachability":"OUTSIDE_CONVEX_HULL","policies":{}}
    target=(sum((v[0] for v in intents),Fraction(0)),sum((v[1] for v in intents),Fraction(0)))
    reach="EXACT_N_SLOT" if target in sumset(actions,n) else "RELAXATION_ONLY"
    avg=(target[0]/n,target[1]/n)
    a_action=nearest(avg,actions)
    a_seq=[a_action]*n
    b_seq=[nearest(v,actions) for v in intents]
    c_seq=carry(intents,actions,case["max_switches"])
    neutral=next((a for a in actions if a[1]==0 and a[2]==0),None)
    if neutral is None:raise ValueError("dictionary lacks common neutral/release slot")
    d_seq=[neutral]*n
    policies={name:metrics(intents,seq,n) for name,seq in (("A_HORIZON_NEAREST",a_seq),("B_INDEPENDENT_ROUND",b_seq),("C_ERROR_CARRY",c_seq),("D_NEUTRAL_SAFE_DEFAULT",d_seq))}
    limit=frac(case["safety_limit_error_sq"])
    if frac(policies["C_ERROR_CARRY"]["worst_prefix_error_sq"])>limit:
        return {"id":case["id"],"disposition":"REFUSE_SAFETY_ENVELOPE","reachability":reach,"policies":policies}
    return {"id":case["id"],"disposition":"COMPILE_OFFLINE","reachability":reach,"policies":policies,"selected_policy":"C_ERROR_CARRY","release_at_tick":n}


def run(data):
    return {"allocation_id":data["allocation_id"],"results":[compile_case(c,data["dictionaries"]) for c in data["cases"]]}


def main():
    p=argparse.ArgumentParser();p.add_argument("--input",required=True);p.add_argument("--output",required=True);a=p.parse_args()
    result=run(json.loads(Path(a.input).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(f"candidate compiled/refused: {len(result['results'])} frozen cases")


if __name__=="__main__":main()
