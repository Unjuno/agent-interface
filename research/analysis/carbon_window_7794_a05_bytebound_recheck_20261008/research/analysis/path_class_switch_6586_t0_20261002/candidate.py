from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def side(points,obstacle):
    crossings=[]
    for p,q in zip(points,points[1:]):
        if min(p[0],q[0])<=0<=max(p[0],q[0]):
            if p[0]==q[0]: crossings.extend((p[1],q[1]))
            else:
                t=-p[0]/(q[0]-p[0]); crossings.append(p[1]+t*(q[1]-p[1]))
    if not crossings:return None
    y=sum(crossings)/len(crossings)
    if y>obstacle[3]:return "UPPER"
    if y<obstacle[1]:return "LOWER"
    return None
def inside(p,r):return r[0]<=p[0]<=r[2] and r[1]<=p[1]<=r[3]
def hit_segment(a,b,r):
    # Independent segment/rectangle edge intersection using orientation predicates.
    if inside(a,r) or inside(b,r):return True
    x0,y0,x1,y1=r; corners=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    def cross(u,v,w):return (v[0]-u[0])*(w[1]-u[1])-(v[1]-u[1])*(w[0]-u[0])
    def on(u,v,w):return min(u[0],v[0])<=w[0]<=max(u[0],v[0]) and min(u[1],v[1])<=w[1]<=max(u[1],v[1])
    for c,d in zip(corners,corners[1:]+corners[:1]):
        ab1,ab2,cd1,cd2=cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
        if ((ab1>0>ab2) or (ab2>0>ab1)) and ((cd1>0>cd2) or (cd2>0>cd1)):return True
        if (ab1==0 and on(a,b,c)) or (ab2==0 and on(a,b,d)) or (cd1==0 and on(c,d,a)) or (cd2==0 and on(c,d,b)):return True
    return False
def blocked(points,bars):return any(hit_segment(a,b,x["rect"]) for a,b in zip(points,points[1:]) for x in bars)
def compatible(prefix,routes,obstacle):
    return sorted({c for pts in routes.values() if pts[:len(prefix)]==prefix for c in [side(pts,obstacle)] if c})
def class_switch(case,obstacle):
    if case["observed_version"]!=case["map_version"]:return dict(decision="REOBSERVE",route_id=None,class_claim=None,reached_goal=False,revisits=0,cost_used=0,route_attempts=[],events=["INVALIDATE_EMBEDDING","YIELD"])
    if not case["branch_visible"]:return dict(decision="UNKNOWN_CLASS",route_id=None,class_claim=None,reached_goal=False,revisits=0,cost_used=0,route_attempts=[],events=["YIELD"])
    routes=case["routes"]; labels={rid:side(pts,obstacle) for rid,pts in routes.items()}; cue=case["blocked_route_claim"]
    last=compatible(case["prior_attempt_prefix"],routes,obstacle); now=compatible(case["current_prefix"],routes,obstacle)
    cue_ok=cue in routes and blocked(routes[cue],case["visible_barriers"])
    empty=dict(route_id=None,class_claim=None,reached_goal=False,revisits=0,cost_used=0,route_attempts=[])
    if cue is not None and not cue_ok:return {**empty,"decision":"UNKNOWN_CLASS","events":["CUE_UNSUPPORTED","YIELD"]}
    if cue_ok and len(last)==1:
        same=[rid for rid,c in labels.items() if c==last[0]]
        if same and all(blocked(routes[rid],case["visible_barriers"]) for rid in same):
            options=[rid for rid in case["policy_order"] if labels.get(rid) and labels[rid]!=last[0] and not blocked(routes[rid],case["visible_barriers"])]
            if options:
                rid=options[0];cost=1+case["route_costs"][rid]
                if cost<=case["event_budget"]:
                    return dict(decision="SCOPED_SWITCH",route_id=rid,class_claim=labels[rid],reached_goal=True,revisits=0,cost_used=cost,route_attempts=[rid],events=["CLASS_BLOCK_CONFIRMED","SELECT_DISTINCT_CLASS","SUBGOAL_REACHED"])
                return {**empty,"decision":"SAFE_YIELD","events":["BUDGET_INSUFFICIENT","YIELD"]}
    distinct={x for x in labels.values() if x}
    if len(routes)>1 and len(distinct)==1 and len(last)==1:
        return {**empty,"decision":"NO_DISTINCT_CLASS_SWITCH","events":["SAME_CLASS_CONTROL","YIELD"]}
    if len(now)!=1:return {**empty,"decision":"UNKNOWN_CLASS","events":["PREFIX_AMBIGUOUS","YIELD"]}
    if len(routes)<2 or len(distinct)<2:return {**empty,"decision":"SAFE_YIELD","events":["NO_ALTERNATIVE_CLASS","YIELD"]}
    return {**empty,"decision":"SAFE_YIELD","events":["NO_SUPPORTED_SWITCH","YIELD"]}
def baseline(case,obstacle,policy):
    remaining=case["event_budget"]; used=0; revisits=0; tried=[]; events=[]; goal=False; chosen=None
    prior=compatible(case["prior_attempt_prefix"],case["routes"],obstacle)
    for rid in case["policy_order"]:
        if rid in case["attempted_route_ids"]:continue
        cost=case["route_costs"][rid]
        is_blocked=blocked(case["routes"][rid],case["visible_barriers"])
        total=cost+(1 if policy=="backtrack" and is_blocked else 0)
        if total>remaining:
            events.append("BUDGET_STOP");break
        remaining-=total;used+=total;tried.append(rid);chosen=rid
        if prior and side(case["routes"][rid],obstacle) in prior:revisits+=1
        events.append("TRY_ROUTE:"+rid)
        if is_blocked:
            events.append("BLOCKED")
            if policy=="backtrack":events.append("BACKTRACK_SHARED_PREFIX")
        else:
            goal=True;events.append("SUBGOAL_REACHED");break
    if not goal and not events:events.append("NO_CANDIDATE_ROUTE")
    return dict(decision="NOVELTY_SEARCH" if policy=="coverage" else "BACKTRACK_SEARCH",route_id=chosen if goal else None,class_claim=None,reached_goal=goal,revisits=revisits,cost_used=used,route_attempts=tried,events=events)
def run(inputs):
    rows=[]
    for case in inputs["cases"]:
        for policy in ("coverage","backtrack","class_aware"):
            out=baseline(case,inputs["obstacle"],policy) if policy!="class_aware" else class_switch(case,inputs["obstacle"])
            rows.append({"case_id":case["case_id"],"policy":policy,**out})
    return {"schema":"path-class-switch-candidate-raw-v1","input_sha256":digest(inputs),"rows":rows}
def main():
    p=argparse.ArgumentParser();p.add_argument("--input",required=True,type=Path);p.add_argument("--output",required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise SystemExit("refusing to overwrite output")
    v=json.loads(a.input.read_text(encoding="utf-8-sig"));raw=run(v);a.output.write_text(json.dumps(raw,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"rows":len(raw["rows"]),"input_sha256":raw["input_sha256"],"output":str(a.output)}))
if __name__=="__main__":main()
