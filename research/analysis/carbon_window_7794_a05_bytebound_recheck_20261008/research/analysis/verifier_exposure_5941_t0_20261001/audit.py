"""Independent raw-only audit for the finite Issue #5941 witness."""
import json, sys

def expected(row):
    eligible=[v["verdict"] for v in row["votes"]
              if v["exposure"]=="none" and v["commit_valid"] is True]
    p=eligible.count("PASS"); f=eligible.count("FAIL")
    if p>=2: return "PASS_SCOPED",eligible
    if f>=2: return "FAIL_SCOPED",eligible
    return "UNKNOWN_INDEPENDENCE",eligible

def audit(doc):
    errors=[]; rows=doc.get("cases")
    if doc.get("schema")!="issue5941-finite-witness-v1" or not isinstance(rows,list):
        return ["schema_or_rows"]
    ids=[r.get("case_id") for r in rows]
    if ids!=[f"{i:03d}" for i in range(len(rows))]: errors.append("ids_or_order")
    if len(rows)!=66: errors.append("row_count")
    for row in rows:
        try:
            disp,eligible=expected(row); got=row["result"]
            if got["disposition"]!=disp: errors.append(row["case_id"]+":disposition")
            if got["independent_first_pass"]!=eligible: errors.append(row["case_id"]+":eligible")
            raw=sum(v["verdict"]=="PASS" for v in row["votes"])>=2
            if got["raw_quorum_pass"] is not raw: errors.append(row["case_id"]+":raw")
        except Exception as e: errors.append(str(row.get("case_id"))+":"+type(e).__name__)
    return errors

if __name__=="__main__":
    with open(sys.argv[1],encoding="utf-8-sig") as handle:
        document=json.load(handle)
    errors=audit(document)
    controls={}
    for name,mutate in {
        "drop_row":lambda d:d["cases"].pop(),
        "reorder":lambda d:d["cases"].reverse(),
        "forge_independence":lambda d:d["cases"][1]["result"].update(disposition="PASS_SCOPED",independent_first_pass=["PASS","PASS"]),
        "change_raw_vote":lambda d:d["cases"][0]["votes"][0].update(verdict="FAIL"),
        "duplicate_id":lambda d:d["cases"][1].update(case_id=d["cases"][0]["case_id"]),
    }.items():
        altered=json.loads(json.dumps(document)); mutate(altered)
        controls[name]=bool(audit(altered))
    print(json.dumps({"audit":"PASS" if not errors and all(controls.values()) else "FAIL",
                      "errors":errors,"controls_rejected":controls},sort_keys=True))
