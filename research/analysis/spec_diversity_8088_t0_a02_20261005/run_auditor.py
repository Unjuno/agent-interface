"""A02 independent raw-only auditor; no candidate-module import."""
import hashlib,json,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
raw=json.loads(Path(sys.argv[1]).read_text())
packet=json.loads((HERE/"CONTRACTS.json").read_text())
matrix=json.loads((HERE/"COVERAGE_MATRIX.json").read_text())
if hashlib.sha256((HERE/"CONTRACTS.json").read_bytes()).hexdigest()!=matrix.get("contracts_sha256"):
    raise SystemExit("contract-byte binding mismatch")
if hashlib.sha256((HERE/"SPEC_A_PRIMARY.json").read_bytes()).hexdigest()!=matrix.get("primary_spec_sha256"):
    raise SystemExit("primary-spec-byte binding mismatch")
contracts={c["id"]:c for c in packet["contracts"]}
names={
"C01_add_work_persists_once":{"postcondition","preexisting_state_unchanged"},
"C02_add_archive_only":{"destination_counts","preexisting_state_unchanged"},
"C03_complete_one_id":{"task2_completed","protected_state_unchanged"},
"C04_rename_preserves_fields":{"task1_renamed","protected_state_unchanged"},
"C05_clear_completed_only":{"completed_removed","active_and_archive_unchanged"},
"C06_filter_is_view_only":{"active_visible_exact","all_visible_exact","records_unchanged"},
"C07_duplicate_title_id_target":{"only_task4_changed"},
"C08_missing_target_unknown":{"unknown_target_no_change"}}
faults={
"C01_add_work_persists_once":"postcondition",
"C02_add_archive_only":"destination_counts",
"C03_complete_one_id":"protected_state_unchanged",
"C06_filter_is_view_only":"all_visible_exact",
"C08_missing_target_unknown":"unknown_target_no_change"}

def derive(r):
    cid,b,a=r["case_id"],r["before"],r["after"]
    w0,w1,ar0,ar1=b["Work"],a["Work"],b["Archive"],a["Archive"]
    if cid=="C01_add_work_persists_once":
        old=[x for x in w1 if x.get("id")!="a02-new"]
        return {"postcondition":sum(x.get("title")=="Plan launch" for x in w1)==1,"preexisting_state_unchanged":old==w0 and ar1==ar0}
    if cid=="C02_add_archive_only":
        old=[x for x in w1 if x.get("id")!="a02-new"]+[x for x in ar1 if x.get("id")!="a02-new"]
        return {"destination_counts":sum(x.get("title")=="Pack kit" for x in ar1)==1 and not any(x.get("title")=="Pack kit" for x in w1),"preexisting_state_unchanged":old==w0+ar0}
    if cid=="C03_complete_one_id":
        old=next(x for x in w0 if x["id"]=="task-2"); new=next((x for x in w1 if x.get("id")=="task-2"),{})
        return {"task2_completed":new.get("completed") is True,"protected_state_unchanged":{k:v for k,v in old.items() if k!="completed"}=={k:v for k,v in new.items() if k!="completed"} and [x for x in w0 if x["id"]!="task-2"]==[x for x in w1 if x.get("id")!="task-2"] and ar0==ar1}
    if cid=="C04_rename_preserves_fields":
        old=next(x for x in w0 if x["id"]=="task-1"); new=next((x for x in w1 if x.get("id")=="task-1"),{})
        return {"task1_renamed":new.get("title")=="Draft v2","protected_state_unchanged":all(new.get(k)==old[k] for k in ("id","completed","due_date")) and [x for x in w0 if x["id"]!="task-1"]==[x for x in w1 if x.get("id")!="task-1"] and ar0==ar1}
    if cid=="C05_clear_completed_only":
        active=[x for x in w0 if x.get("completed") is False]
        return {"completed_removed":all(x.get("completed") is False for x in w1),"active_and_archive_unchanged":w1==active and ar0==ar1}
    if cid=="C06_filter_is_view_only":
        ids=[x["id"] for x in w0]; active=[x["id"] for x in w0 if x.get("completed") is False]; views=r.get("views") or {}
        return {"active_visible_exact":views.get("Active")==active,"all_visible_exact":views.get("All")==ids,"records_unchanged":a==b}
    if cid=="C07_duplicate_title_id_target":
        changed=[dict(x) for x in w1]; target=next((x for x in changed if x.get("id")=="task-4"),None)
        if target is not None: target["completed"]=False
        return {"only_task4_changed":next((x.get("completed") for x in w1 if x.get("id")=="task-4"),False) is True and changed==w0 and ar0==ar1}
    if cid=="C08_missing_target_unknown":return {"unknown_target_no_change":r.get("status")=="UNKNOWN_TARGET" and a==b}
    raise ValueError(cid)

def has_path(obj,path):
    cur=obj
    for part in path.split("."):
        if not isinstance(cur,dict) or part not in cur:return False
        cur=cur[part]
    return True

errors=[]; audited=[]
rows=raw.get("rows",[])
if raw.get("matrix_obligations")!=len(matrix["obligations"]):errors.append("coverage-matrix count mismatch")
for obligation in matrix["obligations"]:
    for row in rows:
        if row.get("case_id")==obligation["case"]:
            for path in obligation["raw_paths"]:
                if not has_path(row,path):errors.append(f"missing raw path {obligation['case']}:{path}")
expected={(cid,"baseline") for cid in contracts}|{(cid,"ordinary_control") for cid in faults}
observed={(r.get("case_id"),r.get("kind")) for r in rows}
if observed!=expected or len(rows)!=len(expected):errors.append("case/kind inventory mismatch")
for row in rows:
    cid=row.get("case_id")
    if cid not in contracts:errors.append(f"unknown contract {cid}");continue
    derived=derive(row)
    if set(derived)!=names[cid]:errors.append(f"predicate inventory mismatch {cid}")
    if derived!=row.get("clause_results"):errors.append(f"candidate/auditor disagreement {cid}/{row.get('kind')}")
    if row.get("accepted")!=all(derived.values()):errors.append(f"acceptance mismatch {cid}/{row.get('kind')}")
    failed={k for k,v in derived.items() if not v}
    if row.get("kind")=="baseline" and failed:errors.append(f"baseline failed {cid}:{sorted(failed)}")
    if row.get("kind")=="ordinary_control":
        expected_clause=faults.get(cid)
        if row.get("fault") is None or row.get("expected_failed_clause")!=expected_clause or failed!={expected_clause}:
            errors.append(f"fault gate mismatch {cid}: expected only {expected_clause}, got {sorted(failed)}")
    audited.append({"case_id":cid,"kind":row.get("kind"),"clauses":len(derived),"failed":sorted(failed)})
print(json.dumps({"schema":"8088-a02-independent-audit-v1","audit":"PASS" if not errors else "FAIL","rows":len(rows),"obligations":len(matrix["obligations"]),"ordinary_controls_rejected":sum(x["kind"]=="ordinary_control" and bool(x["failed"]) for x in audited),"errors":errors,"audited":audited},sort_keys=True,separators=(",",":")))
sys.exit(bool(errors))
