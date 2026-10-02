"""Independent exact arithmetic auditor for #6081; imports no candidate code."""
import argparse
import itertools
import json
from fractions import Fraction
from pathlib import Path


def Q(v):return Fraction(v)
def cross(a,b,p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def convex_vertices(vertices):
    points=sorted(set(vertices))
    if len(points)<3:return points
    lower=[]
    for p in points:
        while len(lower)>1 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    upper=[]
    for p in points[::-1]:
        while len(upper)>1 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]
def contained(point,vertices):
    h=convex_vertices(vertices)
    if len(h)==1:return point==h[0]
    if len(h)==2:return cross(h[0],h[1],point)==0 and all(min(h[0][i],h[1][i])<=point[i]<=max(h[0][i],h[1][i]) for i in range(2))
    edges=[cross(h[i],h[(i+1)%len(h)],point) for i in range(len(h))]
    return min(edges)>=0 or max(edges)<=0
def exact_lattice(actions,n):
    reach={(0,0)}
    for _ in range(n):reach={(x+a[1],y+a[2]) for x,y in reach for a in actions}
    return reach
def norm2(p):return p[0]*p[0]+p[1]*p[1]
def count_changes(seq):return sum(left!=right for left,right in zip(seq,seq[1:]))
def metrics(intents,seq,release_tick):
    goal=(Fraction(0),Fraction(0));pos=(Fraction(0),Fraction(0));errs=[]
    for target,action in zip(intents,seq):
        goal=(goal[0]+target[0],goal[1]+target[1]);pos=(pos[0]+action[1],pos[1]+action[2])
        errs.append(norm2((goal[0]-pos[0],goal[1]-pos[1])))
    return {"actions":[a[0] for a in seq],"switches":count_changes([a[0] for a in seq]),"prefix_error_sq":[str(x) for x in errs],"worst_prefix_error_sq":str(max(errs,default=Fraction(0))),"terminal_error_sq":str(errs[-1] if errs else Fraction(0)),"release_tick":release_tick,"released":True}
def nearest(v,actions):return min(actions,key=lambda a:norm2((v[0]-a[1],v[1]-a[2])))
def independently_carry(intents,actions,budget):
    chosen=[];err=(Fraction(0),Fraction(0));changes=0
    for v in intents:
        pool=actions if not chosen or changes<budget else [a for a in actions if a[0]==chosen[-1][0]]
        a=min(pool,key=lambda z:norm2((err[0]+v[0]-z[1],err[1]+v[1]-z[2])))
        if chosen and a[0]!=chosen[-1][0]:changes+=1
        chosen.append(a);err=(err[0]+v[0]-a[1],err[1]+v[1]-a[2])
    return chosen


def audit(data,raw):
    errors=[];summary=[]; rows={r.get("id"):r for r in raw.get("results",[])}
    if raw.get("allocation_id")!=data.get("allocation_id"):errors.append("allocation identity mismatch")
    if len(rows)!=len(raw.get("results",[])):errors.append("duplicate case ids in raw output")
    improvements=[]; exact_cases=0
    for case in data["cases"]:
        cid=case["id"];r=rows.get(cid);n=len(case["intents"])
        if r is None:errors.append(f"missing result {cid}");continue
        if r.get("disposition")!=case["expected"]:errors.append(f"{cid}: expected disposition {case['expected']}, observed {r.get('disposition')}")
        if r.get("reachability")!=case["reachability"]:errors.append(f"{cid}: exact horizon reachability mismatch")
        if r["disposition"].startswith("REFUSE_"):
            if r.get("release_at_tick",0)!=0:errors.append(f"{cid}: refusal must release immediately")
            if r["disposition"]=="REFUSE_SAFETY_ENVELOPE":
                p=r.get("policies",{});actions=data["dictionaries"][case["dictionary"]]["actions"]
                intents=[(Q(x),Q(y)) for x,y in case["intents"]]
                carry_seq=independently_carry(intents,actions,case["max_switches"])
                expected_c=metrics(intents,carry_seq,len(intents))
                if p.get("C_ERROR_CARRY")!=expected_c:errors.append(f"{cid}: retained offline refusal diagnostic does not match independent carry replay")
                if "selected_policy" in r or "release_at_tick" in r:errors.append(f"{cid}: refused output exposes a compiled/authorized schedule")
                if Q(expected_c["worst_prefix_error_sq"])<=Q(case["safety_limit_error_sq"]):errors.append(f"{cid}: safety refusal not warranted")
            elif r.get("policies") not in ({},None):errors.append(f"{cid}: preflight refusal retained an executable policy schedule")
            summary.append({"id":cid,"disposition":r["disposition"],"trace_count":0})
            continue
        actions=data["dictionaries"][case["dictionary"]]["actions"]
        by_name={a[0]:a for a in actions};intents=[(Q(x),Q(y)) for x,y in case["intents"]]
        vertices=[(a[1],a[2]) for a in actions]
        if any(not contained(v,vertices) for v in intents):errors.append(f"{cid}: compiled an intent outside the legal-action convex hull")
        target=(sum((v[0] for v in intents),Fraction(0)),sum((v[1] for v in intents),Fraction(0)))
        lattice=target in exact_lattice(actions,n)
        if r["reachability"]=="EXACT_N_SLOT" and not lattice:errors.append(f"{cid}: falsely claimed exact N-slot reachability")
        if r["reachability"]=="RELAXATION_ONLY" and lattice:errors.append(f"{cid}: falsely claimed a finite-horizon lattice gap")
        if lattice:exact_cases+=1
        p=r.get("policies",{});required={"A_HORIZON_NEAREST","B_INDEPENDENT_ROUND","C_ERROR_CARRY","D_NEUTRAL_SAFE_DEFAULT"}
        if set(p)!=required:errors.append(f"{cid}: policy inventory mismatch");continue
        avg=(target[0]/n,target[1]/n);a=[nearest(avg,actions)]*n
        b=[nearest(v,actions) for v in intents]
        c=independently_carry(intents,actions,case["max_switches"])
        neutral=next((x for x in actions if x[1]==0 and x[2]==0),None)
        if neutral is None:errors.append(f"{cid}: missing legal neutral/release action");continue
        expected={"A_HORIZON_NEAREST":a,"B_INDEPENDENT_ROUND":b,"C_ERROR_CARRY":c,"D_NEUTRAL_SAFE_DEFAULT":[neutral]*n}
        for name,seq in expected.items():
            observed=p[name]
            if any(action not in by_name for action in observed.get("actions",[])):errors.append(f"{cid}/{name}: illegal action")
            recomputed=metrics(intents,seq,n)
            for key,val in recomputed.items():
                if observed.get(key)!=val:errors.append(f"{cid}/{name}: {key} mismatch")
            if recomputed["switches"]>case["max_switches"]:errors.append(f"{cid}/{name}: switch budget exceeded")
        limit=Q(case["safety_limit_error_sq"])
        cworst=Q(p["C_ERROR_CARRY"]["worst_prefix_error_sq"])
        if r["disposition"]=="COMPILE_OFFLINE":
            if r.get("selected_policy")!="C_ERROR_CARRY" or r.get("release_at_tick")!=n:errors.append(f"{cid}: selected schedule lacks final bounded release")
            if cworst>limit:errors.append(f"{cid}: candidate exceeded prefix safety envelope")
            if r["reachability"]=="EXACT_N_SLOT":
                if any(v not in [(Q(x),Q(y)) for _,x,y in actions] for v in intents):
                    delta=Q(p["A_HORIZON_NEAREST"]["worst_prefix_error_sq"])-cworst
                    terminal_delta=Q(p["A_HORIZON_NEAREST"]["terminal_error_sq"])-Q(p["C_ERROR_CARRY"]["terminal_error_sq"])
                    if delta>0 or terminal_delta>0:improvements.append({"id":cid,"worst_prefix_error_sq_improvement":str(delta),"terminal_error_sq_improvement":str(terminal_delta)})
        elif r["disposition"]=="REFUSE_SAFETY_ENVELOPE":
            if cworst<=limit:errors.append(f"{cid}: spurious safety-envelope refusal")
            if "release_at_tick" in r:errors.append(f"{cid}: refused schedule exposed compile release")
        summary.append({"id":cid,"disposition":r["disposition"],"reachability":r["reachability"],"prefix_error_sq_C":str(cworst),"prefix_error_sq_A":p["A_HORIZON_NEAREST"]["worst_prefix_error_sq"],"terminal_error_sq_C":p["C_ERROR_CARRY"]["terminal_error_sq"],"terminal_error_sq_A":p["A_HORIZON_NEAREST"]["terminal_error_sq"],"release_tick":r.get("release_at_tick"),"switches_C":p["C_ERROR_CARRY"]["switches"],"trace_count":1})
    extras=set(rows)-{c["id"] for c in data["cases"]}
    if extras:errors.append(f"unexpected case ids: {sorted(extras)}")
    if len(improvements)<3:errors.append(f"too few exact-reachable nonrepresentable improvements: {len(improvements)} < 3")
    return {"allocation_id":data["allocation_id"],"disposition":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD_AUDIT","cases":len(data["cases"]),"errors":errors,"independent_improvements":improvements,"summary":summary,"scope":"exact synthetic constant-displacement method fixture only; no GUI/live input or application-effect claim"}


def main():
    p=argparse.ArgumentParser();p.add_argument("--input",required=True);p.add_argument("--candidate",required=True);p.add_argument("--output",required=True);a=p.parse_args()
    result=audit(json.loads(Path(a.input).read_text(encoding="utf-8")),json.loads(Path(a.candidate).read_text(encoding="utf-8")))
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(f"independent audit {result['disposition']}: {result['cases']} cases; {len(result['errors'])} errors; {len(result['independent_improvements'])} improvements")
    raise SystemExit(0 if not result["errors"] else 1)


if __name__=="__main__":main()
