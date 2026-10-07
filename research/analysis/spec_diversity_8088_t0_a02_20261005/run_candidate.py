"""A02 candidate/scorer. Visible-view snapshots are raw, not inferred from records."""
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
packet=json.loads((HERE/"CONTRACTS.json").read_text())
matrix=json.loads((HERE/"COVERAGE_MATRIX.json").read_text())
assert hashlib.sha256((HERE/"CONTRACTS.json").read_bytes()).hexdigest()==matrix["contracts_sha256"]
assert hashlib.sha256((HERE/"SPEC_A_PRIMARY.json").read_bytes()).hexdigest()==matrix["primary_spec_sha256"]

NAMES={
"C01_add_work_persists_once":["postcondition","preexisting_state_unchanged"],
"C02_add_archive_only":["destination_counts","preexisting_state_unchanged"],
"C03_complete_one_id":["task2_completed","protected_state_unchanged"],
"C04_rename_preserves_fields":["task1_renamed","protected_state_unchanged"],
"C05_clear_completed_only":["completed_removed","active_and_archive_unchanged"],
"C06_filter_is_view_only":["active_visible_exact","all_visible_exact","records_unchanged"],
"C07_duplicate_title_id_target":["only_task4_changed"],
"C08_missing_target_unknown":["unknown_target_no_change"]}

FAULTS=[
 ("C01_add_work_persists_once","persistence_lost","postcondition"),
 ("C02_add_archive_only","wrong_destination","destination_counts"),
 ("C03_complete_one_id","collateral_edit","protected_state_unchanged"),
 ("C06_filter_is_view_only","all_filter_stays_active","all_visible_exact"),
 ("C08_missing_target_unknown","success_on_absent_target","unknown_target_no_change")]

def snapshot(case, fault=None):
    cid=case["id"]; before=copy.deepcopy(case["initial"]); after=copy.deepcopy(before)
    status="SUCCESS"; views=None
    if cid=="C01_add_work_persists_once":
        if fault!="persistence_lost": after["Work"].append({"id":"a02-new","title":"Plan launch","completed":False,"due_date":None})
    elif cid=="C02_add_archive_only":
        dest="Work" if fault=="wrong_destination" else "Archive"
        after[dest].append({"id":"a02-new","title":"Pack kit","completed":False,"due_date":None})
    elif cid=="C03_complete_one_id":
        next(x for x in after["Work"] if x["id"]=="task-2")["completed"]=True
        if fault=="collateral_edit": next(x for x in after["Work"] if x["id"]=="task-1")["title"]="CORRUPTED"
    elif cid=="C04_rename_preserves_fields":
        next(x for x in after["Work"] if x["id"]=="task-1")["title"]="Draft v2"
    elif cid=="C05_clear_completed_only":
        after["Work"]=[x for x in after["Work"] if not x["completed"]]
    elif cid=="C06_filter_is_view_only":
        ids=[x["id"] for x in before["Work"]]
        active=[x["id"] for x in before["Work"] if not x["completed"]]
        views={"Active":active,"All":active if fault=="all_filter_stays_active" else ids}
    elif cid=="C07_duplicate_title_id_target":
        next(x for x in after["Work"] if x["id"]=="task-4")["completed"]=True
    elif cid=="C08_missing_target_unknown":
        status="SUCCESS" if fault=="success_on_absent_target" else "UNKNOWN_TARGET"
        if fault=="success_on_absent_target": next(x for x in after["Work"] if x["id"]=="task-2")["completed"]=True
    return {"case_id":cid,"before":before,"after":after,"status":status,"views":views}

def score(raw):
    cid=raw["case_id"]; b=raw["before"]; a=raw["after"]; w0=b["Work"]; w1=a["Work"]; ar0=b["Archive"]; ar1=a["Archive"]
    if cid=="C01_add_work_persists_once":
        existing=[x for x in w1 if x.get("id")!="a02-new"]
        return {"postcondition":sum(x.get("title")=="Plan launch" for x in w1)==1,"preexisting_state_unchanged":existing==w0 and ar1==ar0}
    if cid=="C02_add_archive_only":
        old=[x for x in w1 if x.get("id")!="a02-new"]+[x for x in ar1 if x.get("id")!="a02-new"]
        return {"destination_counts":sum(x.get("title")=="Pack kit" for x in ar1)==1 and sum(x.get("title")=="Pack kit" for x in w1)==0,"preexisting_state_unchanged":old==w0+ar0}
    if cid=="C03_complete_one_id":
        x0=next(x for x in w0 if x["id"]=="task-2"); x1=next((x for x in w1 if x.get("id")=="task-2"),{})
        rest0=[x for x in w0 if x["id"]!="task-2"]; rest1=[x for x in w1 if x.get("id")!="task-2"]
        return {"task2_completed":x1.get("completed") is True,"protected_state_unchanged":{k:v for k,v in x0.items() if k!="completed"}=={k:v for k,v in x1.items() if k!="completed"} and rest0==rest1 and ar0==ar1}
    if cid=="C04_rename_preserves_fields":
        x0=next(x for x in w0 if x["id"]=="task-1"); x1=next((x for x in w1 if x.get("id")=="task-1"),{})
        return {"task1_renamed":x1.get("title")=="Draft v2","protected_state_unchanged":all(x1.get(k)==x0[k] for k in ("id","completed","due_date")) and [x for x in w0 if x["id"]!="task-1"]==[x for x in w1 if x.get("id")!="task-1"] and ar0==ar1}
    if cid=="C05_clear_completed_only":
        active=[x for x in w0 if not x["completed"]]
        return {"completed_removed":not any(x["completed"] for x in w1),"active_and_archive_unchanged":w1==active and ar1==ar0}
    if cid=="C06_filter_is_view_only":
        ids=[x["id"] for x in w0]; active=[x["id"] for x in w0 if not x["completed"]]; views=raw["views"]
        return {"active_visible_exact":views.get("Active")==active,"all_visible_exact":views.get("All")==ids,"records_unchanged":a==b}
    if cid=="C07_duplicate_title_id_target":
        changed=copy.deepcopy(w1); target=next((x for x in changed if x.get("id")=="task-4"),None)
        if target: target["completed"]=False
        return {"only_task4_changed":next((x.get("completed") for x in w1 if x.get("id")=="task-4"),False) is True and changed==w0 and ar0==ar1}
    if cid=="C08_missing_target_unknown":
        return {"unknown_target_no_change":raw["status"]=="UNKNOWN_TARGET" and a==b}
    raise ValueError(cid)

def make_row(case,fault=None,expected=None):
    raw=snapshot(case,fault); results=score(raw)
    return {**raw,"kind":"baseline" if fault is None else "ordinary_control","fault":fault,"expected_failed_clause":expected,"clause_results":results,"accepted":all(results.values())}

by_id={c["id"]:c for c in packet["contracts"]}
rows=[make_row(c) for c in packet["contracts"]]
rows.extend(make_row(by_id[cid],fault,clause) for cid,fault,clause in FAULTS)
print(json.dumps({"schema":"8088-a02-raw-v1","matrix_obligations":len(matrix["obligations"]),"rows":rows},sort_keys=True,separators=(",",":")))
