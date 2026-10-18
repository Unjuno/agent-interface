"""A03 candidate/scorer with independent per-list identity and unordered view predicates."""
import copy,hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
packet=json.loads((HERE/"CONTRACTS.json").read_text())
matrix=json.loads((HERE/"COVERAGE_MATRIX.json").read_text())
assert hashlib.sha256((HERE/"CONTRACTS.json").read_bytes()).hexdigest()==matrix["contracts_sha256"]
assert hashlib.sha256((HERE/"SPEC_A_PRIMARY.json").read_bytes()).hexdigest()==matrix["primary_spec_sha256"]

CLAUSES={
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
 ("C02_add_archive_only","move_existing_archive_to_work","preexisting_state_unchanged"),
 ("C03_complete_one_id","collateral_edit","protected_state_unchanged"),
 ("C06_filter_is_view_only","all_filter_stays_active","all_visible_exact"),
 ("C08_missing_target_unknown","success_on_absent_target","unknown_target_no_change")]

def idmap(rows):
    out={}
    for row in rows:
        key=row["id"]
        if key in out: raise ValueError("duplicate item ID")
        out[key]=row
    return out

def state_maps(state):return {name:idmap(rows) for name,rows in state.items()}

def scenario(case,fault=None):
    cid=case["id"]; before=copy.deepcopy(case["initial"]); after=copy.deepcopy(before)
    status="SUCCESS"; views=None
    if cid=="C01_add_work_persists_once":
        if fault!="persistence_lost":after["Work"].append({"id":"a03-new","title":"Plan launch","completed":False,"due_date":None})
    elif cid=="C02_add_archive_only":
        row={"id":"a03-new","title":"Pack kit","completed":False,"due_date":None}
        if fault=="wrong_destination":after["Work"].append(row)
        else:
            after["Archive"].append(row)
            if fault=="move_existing_archive_to_work":
                moved=next(x for x in after["Archive"] if x["id"]=="archive-1")
                after["Archive"].remove(moved);after["Work"].append(moved)
    elif cid=="C03_complete_one_id":
        next(x for x in after["Work"] if x["id"]=="task-2")["completed"]=True
        if fault=="collateral_edit":next(x for x in after["Work"] if x["id"]=="task-1")["title"]="CORRUPTED"
    elif cid=="C04_rename_preserves_fields":next(x for x in after["Work"] if x["id"]=="task-1")["title"]="Draft v2"
    elif cid=="C05_clear_completed_only":after["Work"]=[x for x in after["Work"] if not x["completed"]]
    elif cid=="C06_filter_is_view_only":
        ids=[x["id"] for x in before["Work"]]; active=[x["id"] for x in before["Work"] if not x["completed"]]
        views={"Active":active,"All":active if fault=="all_filter_stays_active" else ids}
    elif cid=="C07_duplicate_title_id_target":next(x for x in after["Work"] if x["id"]=="task-4")["completed"]=True
    elif cid=="C08_missing_target_unknown":
        if fault=="success_on_absent_target":
            status="SUCCESS";next(x for x in after["Work"] if x["id"]=="task-2")["completed"]=True
        else:status="UNKNOWN_TARGET"
    return {"case_id":cid,"before":before,"after":after,"status":status,"views":views}

def same_except_new(before,after):
    left=state_maps(before);right=state_maps(after)
    for name in left:
        right[name].pop("a03-new",None);left[name].pop("a03-new",None)
    return left==right

def score(r):
    cid=r["case_id"];b=r["before"];a=r["after"];bm=state_maps(b);am=state_maps(a)
    w0,w1=b["Work"],a["Work"];ar0,ar1=b["Archive"],a["Archive"]
    if cid=="C01_add_work_persists_once":
        return {"postcondition":sum(x.get("title")=="Plan launch" for x in w1)==1,"preexisting_state_unchanged":same_except_new(b,a)}
    if cid=="C02_add_archive_only":
        return {"destination_counts":sum(x.get("title")=="Pack kit" for x in ar1)==1 and sum(x.get("title")=="Pack kit" for x in w1)==0,"preexisting_state_unchanged":same_except_new(b,a)}
    if cid=="C03_complete_one_id":
        old=bm["Work"]["task-2"];new=am["Work"].get("task-2",{})
        protect={k:v for k,v in old.items() if k!="completed"}=={k:v for k,v in new.items() if k!="completed"}
        oldrest={k:v for k,v in bm["Work"].items() if k!="task-2"};newrest={k:v for k,v in am["Work"].items() if k!="task-2"}
        return {"task2_completed":new.get("completed") is True,"protected_state_unchanged":protect and oldrest==newrest and bm["Archive"]==am["Archive"]}
    if cid=="C04_rename_preserves_fields":
        old=bm["Work"]["task-1"];new=am["Work"].get("task-1",{})
        preserve=all(new.get(k)==old[k] for k in ("id","completed","due_date"))
        oldrest={k:v for k,v in bm["Work"].items() if k!="task-1"};newrest={k:v for k,v in am["Work"].items() if k!="task-1"}
        return {"task1_renamed":new.get("title")=="Draft v2","protected_state_unchanged":preserve and oldrest==newrest and bm["Archive"]==am["Archive"]}
    if cid=="C05_clear_completed_only":
        active={k:v for k,v in bm["Work"].items() if v.get("completed") is False}
        return {"completed_removed":all(x.get("completed") is False for x in w1),"active_and_archive_unchanged":am["Work"]==active and am["Archive"]==bm["Archive"]}
    if cid=="C06_filter_is_view_only":
        ids=set(bm["Work"]);active={k for k,v in bm["Work"].items() if v.get("completed") is False};views=r.get("views") or {}
        return {"active_visible_exact":len(views.get("Active",[]))==len(set(views.get("Active",[]))) and set(views.get("Active",[]))==active,
                "all_visible_exact":len(views.get("All",[]))==len(set(views.get("All",[]))) and set(views.get("All",[]))==ids,
                "records_unchanged":bm==am}
    if cid=="C07_duplicate_title_id_target":
        changed=copy.deepcopy(am);target=changed["Work"].get("task-4")
        if target:target["completed"]=bm["Work"]["task-4"]["completed"]
        return {"only_task4_changed":am["Work"].get("task-4",{}).get("completed") is True and changed==bm}
    if cid=="C08_missing_target_unknown":return {"unknown_target_no_change":r["status"]=="UNKNOWN_TARGET" and bm==am}
    raise ValueError(cid)

def emit(case,fault=None,expected=None):
    raw=scenario(case,fault);out=score(raw)
    return {**raw,"kind":"baseline" if fault is None else "ordinary_control","fault":fault,"expected_failed_clause":expected,"clause_results":out,"accepted":all(out.values())}

byid={x["id"]:x for x in packet["contracts"]}
rows=[emit(c) for c in packet["contracts"]]
rows.extend(emit(byid[cid],fault,clause) for cid,fault,clause in FAULTS)
print(json.dumps({"schema":"8088-a03-raw-v1","coverage_obligations":len(matrix["obligations"]),"rows":rows},sort_keys=True,separators=(",",":")))
