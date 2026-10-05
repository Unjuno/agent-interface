"""Independent exact oracle auditor; does not import candidate implementation."""
import itertools,json,sys

def multiply(l,r):
    a,b,c,d,x,y=l; A,B,C,D,X,Y=r
    return [a*A+b*C,a*B+b*D,c*A+d*C,c*B+d*D,a*X+b*Y+x,c*X+d*Y+y]
def transform(p,m):
    a,b,c,d,x,y=m; return [a*p[0]+b*p[1]+x,c*p[0]+d*p[1]+y]
def corners(box,delta=(0,0)):
    x1,y1,x2,y2=box; dx,dy=delta
    return [[x1+dx,y1+dy],[x2+dx,y1+dy],[x2+dx,y2+dy],[x1+dx,y2+dy]]
def hull_rect(points): return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
def point_bounds(points): return [[min(p[i] for p in points),max(p[i] for p in points)] for i in (0,1)]
def contains(point,poly):
    signs=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        v=(b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])
        if v: signs.append(1 if v>0 else -1)
    b=hull_rect(poly)
    return not (1 in signs and -1 in signs) and b[0]<=point[0]<=b[2] and b[1]<=point[1]<=b[3]
def find_paths(edges,start,end,unit,context):
    found=[]
    def visit(node,used,seq):
        if node==end: found.append(seq); return
        for i,e in enumerate(edges):
            if i in used or e["unit"]!=unit or e["context"]!=context: continue
            if (e["source"]["frame"],e["source"]["epoch"])==node:
                visit((e["target"]["frame"],e["target"]["epoch"]),used|{i},seq+[e])
    visit((start["frame"],start["epoch"]),set(),[]); return found
def total_matrix(path,assignment):
    t=[1,0,0,1,0,0]
    for edge in path: t=multiply(assignment[edge["id"]],t)
    return t
def outcome(worlds):
    return "ADMIT" if worlds and all(contains(w["point"],w["target"]) and not any(contains(w["point"],p) for p in w["forbidden"]) for w in worlds) else "UNKNOWN"
def hulls(worlds):
    return {"point_bounds":point_bounds([w["point"] for w in worlds]),"target_bounds":hull_rect([p for w in worlds for p in w["target"]])}

def exact_worlds(c,truth):
    goal=(c["input"]["frame"],c["input"]["epoch"])
    tp=find_paths(c["edges"],c["target"]["at"],goal,c["required_unit"],c["required_context"])
    ap=find_paths(c["edges"],c["action"]["at"],goal,c["required_unit"],c["required_context"])
    fpaths=[find_paths(c["edges"],f["at"],goal,c["required_unit"],c["required_context"]) for f in c["forbidden"]]
    if len(tp)!=1 or len(ap)!=1 or any(len(p)!=1 for p in fpaths): return None
    all_worlds=[]
    for assignment in truth["edge_assignments"]:
        tm=total_matrix(tp[0],assignment); am=total_matrix(ap[0],assignment)
        for target_box,action_pt,te,ae in itertools.product(truth["target_boxes"],truth["action_points"],truth["target_errors"],truth["action_errors"]):
            target_poly=[transform(p,tm) for p in corners(target_box,te)]
            action=transform([action_pt[0]+ae[0],action_pt[1]+ae[1]],am)
            forb=[]
            for j,fb in enumerate(truth["forbidden_boxes"]): forb.append([transform(p,total_matrix(fpaths[j][0],assignment)) for p in corners(fb)])
            all_worlds.append({"point":action,"target":target_poly,"forbidden":forb})
    return all_worlds

def baseline_worlds(c,state):
    m=state; worlds=[]
    for te,ae in itertools.product(c["target_error_options"],c["action_error_options"]):
        poly=[transform(p,m) for p in corners(c["target"]["box"],te)]
        point=transform([c["action"]["point"][0]+ae[0],c["action"]["point"][1]+ae[1]],m)
        forb=[[transform(p,m) for p in corners(f["box"])] for f in c["forbidden"]]
        worlds.append({"point":point,"target":poly,"forbidden":forb})
    return worlds

def audit(public,oracle,candidate):
    cases=public["cases"]; truths=oracle["worlds"]; rows=candidate.get("rows",[])
    errors=[]; ids=[r.get("case_id") for r in rows]; expected_ids=[c["case_id"] for c in cases]
    if len(ids)!=len(set(ids)) or set(ids)!=set(expected_ids): errors.append("candidate_row_integrity")
    by_id={r.get("case_id"):r for r in rows}; state=public["baseline_schedule"]["initial_state"]
    graph_false_admit=0; graph_false_unknown=0; baseline_false_unknown=0; exact_safe_composed=0; invalids=0; invalid_fail=0; summaries=[]
    for c in cases:
        cid=c["case_id"]; t=truths[cid]; r=by_id.get(cid)
        if r is None: errors.append(cid+":missing_candidate_row"); continue
        if c.get("calibration_event"): state=c["calibration_event"]["refresh_to"]
        if r.get("baseline",{}).get("state_used")!=state: errors.append(cid+":baseline_schedule_mismatch")
        bw=baseline_worlds(c,public["baseline_schedule"]["calibrations"][state]); bh=hulls(bw); bd=outcome(bw)
        if r.get("baseline",{}).get("decision")!=bd or r.get("baseline",{}).get("point_bounds")!=bh["point_bounds"] or r.get("baseline",{}).get("target_bounds")!=bh["target_bounds"]:
            errors.append(cid+":baseline_output_mismatch")
        if t.get("expected_invalid"):
            invalids+=1
            if r.get("decision")=="UNKNOWN": invalid_fail+=1
            else: errors.append(cid+":invalid_not_unknown")
            continue
        exact=exact_worlds(c,t)
        if exact is None: errors.append(cid+":valid_fixture_path_not_unique"); continue
        expected=hulls(exact); expected_decision=outcome(exact)
        if r.get("point_bounds")!=expected["point_bounds"]: errors.append(cid+":point_mapping_mismatch")
        if r.get("target_bounds")!=expected["target_bounds"]: errors.append(cid+":target_mapping_mismatch")
        if r.get("decision")!=expected_decision: errors.append(cid+":decision_oracle_mismatch")
        safe=expected_decision=="ADMIT"
        if r.get("decision")=="ADMIT" and not safe:
            graph_false_admit+=1; errors.append(cid+":false_admission")
        if t.get("stratum")=="composed_valid" and safe:
            exact_safe_composed+=1
            graph_false_unknown+=int(r.get("decision")=="UNKNOWN")
            baseline_false_unknown+=int(bd=="UNKNOWN")
        summaries.append({"case_id":cid,"exact_decision":expected_decision,"graph":r.get("decision"),"baseline":bd,"mapped_point_bounds":expected["point_bounds"],"mapped_target_bounds":expected["target_bounds"]})
    reduction=(baseline_false_unknown-graph_false_unknown)/baseline_false_unknown if baseline_false_unknown else 0.0
    # Verify the hand-checkable shear identity and the explicitly chained epochs.
    shear=next(c for c in cases if c["case_id"]=="INVERSE_SHEAR_PAIR_IDENTITY")
    sw=truths[shear["case_id"]]["edge_assignments"][0]; sm=total_matrix(shear["edges"],sw)
    if sm != [1,0,0,1,0,0]: errors.append("inverse_shear_product_not_identity")
    epoch=next(c for c in cases if c["case_id"]=="COMPOSE_EPOCH_7_8_9")
    epoch_path=find_paths(epoch["edges"],epoch["target"]["at"],(epoch["input"]["frame"],epoch["input"]["epoch"]),epoch["required_unit"],epoch["required_context"])
    transition=[[e["source"]["epoch"],e["target"]["epoch"]] for e in epoch_path[0]] if len(epoch_path)==1 else []
    if transition != [[7,8],[8,9]]: errors.append("epoch_transition_not_7_8_9")
    passed=(not errors and graph_false_admit==0 and invalid_fail==invalids and exact_safe_composed>0 and reduction>=0.20)
    return {"disposition":"PASS_METHOD_SCOPED" if passed else "FAIL_METHOD","errors":errors,"summary":{"cases":len(cases),"exact_safe_composed":exact_safe_composed,"graph_false_unknown_composed":graph_false_unknown,"baseline_false_unknown_composed":baseline_false_unknown,"composed_false_unknown_reduction":reduction,"false_admissions":graph_false_admit,"invalid_controls":invalids,"invalid_fail_closed":invalid_fail,"inverse_shear_identity_verified":sm==[1,0,0,1,0,0],"epoch_path":transition},"cases":summaries}

if __name__=="__main__":
    public=json.load(open(sys.argv[1])); oracle=json.load(open(sys.argv[2])); candidate=json.load(open(sys.argv[3])); result=audit(public,oracle,candidate)
    open(sys.argv[4],"w").write(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result["summary"],sort_keys=True)); print(result["disposition"]); sys.exit(0 if result["disposition"]=="PASS_METHOD_SCOPED" else 2)
