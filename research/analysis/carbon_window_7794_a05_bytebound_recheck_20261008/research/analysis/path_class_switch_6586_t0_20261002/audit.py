from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

def sha(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def in_box(p,r):return r[0]<=p[0]<=r[2] and r[1]<=p[1]<=r[3]
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def point_between(a,b,p):return min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1])
def intersects(a,b,box):
    if in_box(a,box) or in_box(b,box):return True
    l,bottom,r,top=box;corners=[(l,bottom),(r,bottom),(r,top),(l,top)]
    for c,d in zip(corners,corners[1:]+corners[:1]):
        x,y,z,w=cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
        if ((x>0>y)or(y>0>x))and((z>0>w)or(w>0>z)):return True
        if (x==0 and point_between(a,b,c))or(y==0 and point_between(a,b,d))or(z==0 and point_between(c,d,a))or(w==0 and point_between(c,d,b)):return True
    return False
def hits(points,bars):return any(intersects(a,b,k["rect"]) for a,b in zip(points,points[1:]) for k in bars)
def topology(points,ob):
    ys=[]
    for a,b in zip(points,points[1:]):
        if a[0]<0<b[0] or b[0]<0<a[0]:ys.append(a[1]+(-a[0])*(b[1]-a[1])/(b[0]-a[0]))
        elif a[0]==0:ys.append(a[1])
        elif b[0]==0:ys.append(b[1])
    if not ys:return None
    y=ys[0]
    return "UPPER" if y>ob[3] else ("LOWER" if y<ob[1] else None)
def prefix_set(prefix,routes,ob):return sorted({c for pts in routes.values() if pts[:len(prefix)]==prefix for c in [topology(pts,ob)] if c})
def independent_baseline(case,ob,policy):
    left=case["event_budget"];spent=0;revisit=0;attempted=[];events=[];success=False;route=None;prior=prefix_set(case["prior_attempt_prefix"],case["routes"],ob)
    for rid in case["policy_order"]:
        if rid in case["attempted_route_ids"]:continue
        cost=case["route_costs"][rid];blocked_now=hits(case["routes"][rid],case["visible_barriers"]);need=cost+(1 if policy=="backtrack" and blocked_now else 0)
        if need>left:events.append("BUDGET_STOP");break
        left-=need;spent+=need;attempted.append(rid);route=rid
        if prior and topology(case["routes"][rid],ob) in prior:revisit+=1
        events.append("TRY_ROUTE:"+rid)
        if blocked_now:
            events.append("BLOCKED")
            if policy=="backtrack":events.append("BACKTRACK_SHARED_PREFIX")
        else:success=True;events.append("SUBGOAL_REACHED");break
    if not success and not events:events.append("NO_CANDIDATE_ROUTE")
    return spent,revisit,attempted,success,route if success else None,events
def audit(inputs,oracle,raw):
    errors=[]
    if raw.get("schema")!="path-class-switch-candidate-raw-v1" or raw.get("input_sha256")!=sha(inputs):errors.append("binding_or_schema")
    rows=raw.get("rows",[]);ix={(r.get("case_id"),r.get("policy")):r for r in rows};keys={(c["case_id"],p)for c in inputs["cases"]for p in("coverage","backtrack","class_aware")}
    if len(rows)!=len(keys)or set(ix)!=keys:errors.append("row_coverage_or_identity")
    truth=oracle.get("case_truth",{})
    for case in inputs["cases"]:
        cid=case["case_id"];routes=case["routes"];labels={rid:topology(path,inputs["obstacle"])for rid,path in routes.items()}; c=ix.get((cid,"class_aware"))
        if c is None:continue
        expected=truth.get(cid,{}).get("required")
        if c.get("decision")!=expected:errors.append("class_gate:"+cid)
        if c.get("cost_used",-1)<0 or c.get("cost_used",999)>case["event_budget"]:errors.append("budget:"+cid)
        if c.get("route_id") is not None:
            rid=c["route_id"]
            if rid not in routes or c.get("class_claim")!=labels.get(rid):errors.append("class_label:"+cid)
            elif hits(routes[rid],case["visible_barriers"]):errors.append("selected_path_blocked:"+cid)
        for policy in ("coverage","backtrack"):
            r=ix.get((cid,policy))
            if r is None:continue
            spent,revisit,attempted,success,route,events=independent_baseline(case,inputs["obstacle"],policy)
            if (r.get("cost_used"),r.get("revisits"),r.get("route_attempts"),r.get("reached_goal"),r.get("route_id"),r.get("events"))!=(spent,revisit,attempted,success,route,events):errors.append("baseline_replay:"+cid+":"+policy)
        if cid=="blocked_class_positive":
            last=prefix_set(case["prior_attempt_prefix"],routes,inputs["obstacle"]);same=[rid for rid,k in labels.items()if k=="UPPER"]
            all_blocked=bool(same)and all(hits(routes[rid],case["visible_barriers"])for rid in same)
            safe=[rid for rid,k in labels.items()if k=="LOWER"and not hits(routes[rid],case["visible_barriers"])]
            b=ix.get((cid,"backtrack"),{});v=ix.get((cid,"coverage"),{})
            if last!=["UPPER"]or not all_blocked or not safe:errors.append("positive_embedded_geometry")
            if c.get("route_id")!=safe[0]or c.get("cost_used")!=oracle["policy_expectations"][cid]["class_aware_cost"]or not c.get("reached_goal")or c.get("revisits")!=0:errors.append("positive_class_switch")
            if v.get("reached_goal")or b.get("reached_goal")or v.get("revisits",0)<=c.get("revisits",0)or b.get("revisits",0)<=c.get("revisits",0):errors.append("positive_gain_missing")
        elif cid=="shared_prefix_ambiguous":
            if prefix_set(case["current_prefix"],routes,inputs["obstacle"])!=["LOWER","UPPER"]or c.get("route_id")is not None:errors.append("ambiguous_prefix")
        elif cid=="same_class_deceptive_branch":
            if set(labels.values())!={"UPPER"}or c.get("decision")!="NO_DISTINCT_CLASS_SWITCH"or c.get("route_id")is not None:errors.append("same_class_control")
        elif cid=="geometry_revision":
            if case["map_version"]==case["observed_version"]or c.get("events")!=["INVALIDATE_EMBEDDING","YIELD"]:errors.append("revision_control")
        elif cid=="false_class_cue":
            rid=case["blocked_route_claim"]
            if any(hits(routes[rid],[b])for b in case["visible_barriers"])or c.get("decision")!="UNKNOWN_CLASS"or c.get("route_id")is not None:errors.append("false_cue_control")
        elif cid=="single_class_graph":
            if len(set(labels.values()))!=1 or c.get("decision")!="SAFE_YIELD"or c.get("route_id")is not None:errors.append("single_class_control")
        for pol in ("coverage","backtrack","class_aware"):
            r=ix.get((cid,pol))
            if r and any(k in r for k in ("oracle_class","hidden_map","full_topology","case_truth")):errors.append("privileged_leak:"+cid+":"+pol)
    return {"schema":"path-class-switch-audit-v1","raw_sha256":sha(raw),"rows_replayed":len(ix),"errors":errors,"disposition":"PASS_METHOD_SCOPED"if not errors else"FAIL_AUDIT"}
def main():
    p=argparse.ArgumentParser();p.add_argument("--input",required=True);p.add_argument("--oracle",required=True);p.add_argument("--raw",required=True);p.add_argument("--output",required=True);a=p.parse_args();out=Path(a.output)
    if out.exists():raise SystemExit("refusing to overwrite output")
    r=audit(*(json.loads(Path(x).read_text(encoding="utf-8-sig"))for x in(a.input,a.oracle,a.raw)));out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n",encoding="utf-8");print(json.dumps({"disposition":r["disposition"],"rows_replayed":r["rows_replayed"],"errors":len(r["errors"])}));raise SystemExit(0 if r["disposition"]=="PASS_METHOD_SCOPED"else 1)
if __name__=="__main__":main()
