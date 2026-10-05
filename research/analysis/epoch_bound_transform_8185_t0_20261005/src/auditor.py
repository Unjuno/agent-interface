"""Independent exact finite-world auditor; deliberately does not import candidate."""
import itertools,json,sys

def paths(es,s,d,epoch,unit,ctx):
    found=[]
    def rec(n,seen,chain):
        if n==d: found.append(chain); return
        for i,e in enumerate(es):
            if i not in seen and e["src"]==n and e["epoch"]==epoch and e["unit"]==unit and e["context"]==ctx:
                rec(e["dst"],seen|{i},chain+[e])
    rec(s,set(),[]); return found

def map_point(p, chain, selected):
    x,y=p
    for e in chain:
        t=selected[e["id"]]; x,y=t["sx"]*x+t["tx"],t["sy"]*y+t["ty"]
    return x,y

def inside(p,b): return b[0]<=p[0]<=b[2] and b[1]<=p[1]<=b[3]

def audit(public_path, oracle_path, candidate_path):
    pubs=[json.loads(x) for x in open(public_path) if x.strip()]
    truth=json.load(open(oracle_path)); raw_rows=[json.loads(x) for x in open(candidate_path) if x.strip()]
    raw={r["case_id"]:r for r in raw_rows}
    errors=[]; valid_safe=0; baseline_unknown=0; graph_unknown=0; false_admit=0; invalid_total=0; invalid_fail_closed=0; per=[]
    expected={c["case_id"] for c in pubs}
    if len(raw_rows)!=len(expected) or len(raw)!=len(raw_rows) or set(raw)!=expected: errors.append("candidate_row_integrity")
    for c in pubs:
        cid=c["case_id"]; o=truth[cid]; r=raw.get(cid)
        if r is None: errors.append(cid+":missing_output"); continue
        # Candidate invalid handling and exact path reconstruction are separately checked.
        if not o["valid"]:
            invalid_total+=1
            safe_invalid = r.get("graph")=="UNKNOWN"
            invalid_fail_closed += int(safe_invalid)
            if not safe_invalid: errors.append(cid+":invalid_not_fail_closed")
            continue
        tp=paths(c["edges"],c["target"]["frame"],"input",c["epoch"],c["unit"],c["context"])
        ap=paths(c["edges"],c["action"]["frame"],"input",c["epoch"],c["unit"],c["context"])
        if len(tp)!=1 or len(ap)!=1:
            errors.append(cid+":fixture_path_not_unique"); continue
        keys=sorted(o["edge_options"]); domains=[o["edge_options"][k] for k in keys]; safe=True
        for values in itertools.product(*domains):
            sel=dict(zip(keys,values)); box=c["target"]["box"]
            corners=[map_point([box[0],box[1]],tp[0],sel),map_point([box[2],box[3]],tp[0],sel)]
            mapped=[min(p[0] for p in corners),min(p[1] for p in corners),max(p[0] for p in corners),max(p[1] for p in corners)]
            p=map_point(c["action"]["point"],ap[0],sel)
            safe &= inside(p,mapped) and not any(inside(p,[*map_point([b[0],b[1]],tp[0],sel),*map_point([b[2],b[3]],tp[0],sel)]) for b in c.get("forbidden",[]))
        if safe:
            valid_safe+=1
            if r.get("graph")!="ADMIT": graph_unknown+=1
            if r.get("baseline")=="UNKNOWN": baseline_unknown+=1
        elif r.get("graph")=="ADMIT":
            false_admit+=1; errors.append(cid+":false_admit")
        per.append({"case_id":cid,"exact_safe":safe,"graph":r.get("graph"),"baseline":r.get("baseline")})
    reduction=(baseline_unknown-graph_unknown)/baseline_unknown if baseline_unknown else 0.0
    composed=[p for p in per if next(c for c in pubs if c["case_id"]==p["case_id"])["kind"]=="composed" and p["exact_safe"]]
    # Baseline is intentionally unavailable for these composed cases; count candidate graph admissions.
    composed_gain=sum(p["graph"]=="ADMIT" for p in composed)
    cb=sum(p["baseline"]=="UNKNOWN" for p in composed); cg=sum(p["graph"]=="UNKNOWN" for p in composed)
    composed_reduction=(cb-cg)/cb if cb else 0.0
    disposition="PASS_METHOD_SCOPED" if not errors and false_admit==0 and invalid_fail_closed==invalid_total and len(composed)>=3 and composed_reduction>=0.20 else "FAIL_METHOD"
    return {"disposition":disposition,"errors":errors,"summary":{"valid_exact_safe":valid_safe,"graph_false_unknown":graph_unknown,"baseline_false_unknown":baseline_unknown,"baseline_false_unknown_reduction":reduction,"composed_safe_cases":len(composed),"composed_graph_admitted":composed_gain,"composed_baseline_false_unknown":cb,"composed_graph_false_unknown":cg,"composed_false_unknown_reduction":composed_reduction,"false_admissions":false_admit,"invalid_controls":invalid_total,"invalid_fail_closed":invalid_fail_closed},"cases":per}

if __name__=="__main__":
    result=audit(*sys.argv[1:4]); open(sys.argv[4],"w").write(json.dumps(result,sort_keys=True,indent=2)+"\n"); print(json.dumps(result["summary"],sort_keys=True)); print(result["disposition"]); sys.exit(0 if result["disposition"]=="PASS_METHOD_SCOPED" else 2)
