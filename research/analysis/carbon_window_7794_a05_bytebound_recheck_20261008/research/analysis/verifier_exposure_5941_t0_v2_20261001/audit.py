"""Independent raw-only auditor and effective corruption controls."""
import copy, json, sys

def derive(votes):
    eligible=[]
    for v in votes:
        if v.get("exposure")=="none" and type(v.get("commit_valid")) is bool and v["commit_valid"]:
            eligible.append(v.get("verdict"))
    p,f=eligible.count("PASS"),eligible.count("FAIL")
    disposition="PASS_SCOPED" if p>=2 else "FAIL_SCOPED" if f>=2 else "UNKNOWN_INDEPENDENCE"
    return {"raw_quorum_pass":sum(v.get("verdict")=="PASS" for v in votes)>=2,
            "scoped_quorum_pass":disposition=="PASS_SCOPED",
            "independent_first_pass":eligible,"disposition":disposition}

def audit(doc):
    errors=[]
    if doc.get("schema")!="issue5941-finite-witness-v2": return ["schema"]
    rows=doc.get("cases")
    if not isinstance(rows,list): return ["rows"]
    if len(rows)!=66: errors.append("row_count")
    ids=[r.get("case_id") for r in rows]
    if ids!=[f"{i:03d}" for i in range(len(rows))]: errors.append("id_or_order")
    for row in rows:
        try:
            if row.get("result")!=derive(row["votes"]): errors.append(row.get("case_id","?")+":derived_result")
            if len(row["votes"])!=3 or [v.get("verifier") for v in row["votes"]]!=["V1","V2","V3"]:
                errors.append(row.get("case_id","?")+":verifier_inventory")
        except Exception as exc: errors.append(row.get("case_id","?")+":"+type(exc).__name__)
    return errors

def corruption_controls(doc):
    def change_exposed_pass_to_unexposed(d):
        for row in d["cases"]:
            v=row["votes"]
            if row["truth"]=="FAIL" and [x["verdict"] for x in v]==["PASS","PASS","FAIL"] and v[1]["exposure"]=="peer_verdict" and v[1]["commit_valid"]:
                v[1]["exposure"]="none"; return
        raise AssertionError("copied-vote witness absent")
    def invalidate_required_commit(d):
        for row in d["cases"]:
            v=row["votes"]
            if row["truth"]=="FAIL" and [x["verdict"] for x in v]==["PASS","PASS","FAIL"] and v[1]["exposure"]=="none" and v[1]["commit_valid"]:
                v[1]["commit_valid"]=False; return
        raise AssertionError("commit witness absent")
    mutations={
      "drop_row":lambda d:d["cases"].pop(),
      "reorder_rows":lambda d:d["cases"].reverse(),
      "promote_exposed_vote":change_exposed_pass_to_unexposed,
      "invalidate_commit":invalidate_required_commit,
      "falsify_disposition":lambda d:d["cases"][0]["result"].update(disposition="UNKNOWN_INDEPENDENCE",scoped_quorum_pass=False),
      "duplicate_id":lambda d:d["cases"][1].update(case_id=d["cases"][0]["case_id"]),
    }
    outcomes={}
    for name,mutate in mutations.items():
        altered=copy.deepcopy(doc); mutate(altered); outcomes[name]=bool(audit(altered))
    return outcomes

if __name__=="__main__":
    with open(sys.argv[1],encoding="utf-8-sig") as f: doc=json.load(f)
    errors=audit(doc); controls=corruption_controls(doc)
    result={"audit":"PASS" if not errors and all(controls.values()) else "FAIL",
            "errors":errors,"controls_rejected":controls}
    print(json.dumps(result,sort_keys=True))
    if result["audit"]!="PASS": sys.exit(1)
