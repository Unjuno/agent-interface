"""A03 raw-only audit; independently authored and never imports candidate code."""
import copy,hashlib,json,sys
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
raw=json.loads(Path(sys.argv[1]).read_text())
contracts=json.loads((HERE/"CONTRACTS.json").read_text())
primary=json.loads((HERE/"SPEC_A_PRIMARY.json").read_text())
matrix=json.loads((HERE/"COVERAGE_MATRIX.json").read_text())
if hashlib.sha256((HERE/"CONTRACTS.json").read_bytes()).hexdigest()!=matrix.get("contracts_sha256"):raise SystemExit("contract digest mismatch")
if hashlib.sha256((HERE/"SPEC_A_PRIMARY.json").read_bytes()).hexdigest()!=matrix.get("primary_spec_sha256"):raise SystemExit("primary decomposition digest mismatch")
byid={c["id"]:c for c in contracts["contracts"]}
clause_names={
"C01_add_work_persists_once":{"postcondition","preexisting_state_unchanged"},
"C02_add_archive_only":{"destination_counts","preexisting_state_unchanged"},
"C03_complete_one_id":{"task2_completed","protected_state_unchanged"},
"C04_rename_preserves_fields":{"task1_renamed","protected_state_unchanged"},
"C05_clear_completed_only":{"completed_removed","active_and_archive_unchanged"},
"C06_filter_is_view_only":{"active_visible_exact","all_visible_exact","records_unchanged"},
"C07_duplicate_title_id_target":{"only_task4_changed"},
"C08_missing_target_unknown":{"unknown_target_no_change"}}
control_map={
 ("C01_add_work_persists_once","persistence_lost"):"postcondition",
 ("C02_add_archive_only","wrong_destination"):"destination_counts",
 ("C02_add_archive_only","move_existing_archive_to_work"):"preexisting_state_unchanged",
 ("C03_complete_one_id","collateral_edit"):"protected_state_unchanged",
 ("C06_filter_is_view_only","all_filter_stays_active"):"all_visible_exact",
 ("C08_missing_target_unknown","success_on_absent_target"):"unknown_target_no_change"}

def records(state):
    result={}
    for list_name,items in state.items():
        indexed={item["id"]:item for item in items}
        if len(indexed)!=len(items):raise ValueError("duplicate IDs in raw state")
        result[list_name]=indexed
    return result

def eq_without_added(old,new):
    x=records(old);y=records(new)
    for m in (x,y):
        for items in m.values():items.pop("a03-new",None)
    return x==y

def derive(row):
    cid=row["case_id"];before=row["before"];after=row["after"]
    x=records(before);y=records(after);w0,w1=before["Work"],after["Work"]
    a0,a1=before["Archive"],after["Archive"]
    if cid=="C01_add_work_persists_once":
        return {"postcondition":sum(t.get("title")=="Plan launch" for t in w1)==1,"preexisting_state_unchanged":eq_without_added(before,after)}
    if cid=="C02_add_archive_only":
        return {"destination_counts":sum(t.get("title")=="Pack kit" for t in a1)==1 and not any(t.get("title")=="Pack kit" for t in w1),"preexisting_state_unchanged":eq_without_added(before,after)}
    if cid=="C03_complete_one_id":
        old=x["Work"]["task-2"];new=y["Work"].get("task-2",{})
        keep={k:v for k,v in old.items() if k!="completed"}=={k:v for k,v in new.items() if k!="completed"}
        restold={k:v for k,v in x["Work"].items() if k!="task-2"};restnew={k:v for k,v in y["Work"].items() if k!="task-2"}
        return {"task2_completed":new.get("completed") is True,"protected_state_unchanged":keep and restold==restnew and x["Archive"]==y["Archive"]}
    if cid=="C04_rename_preserves_fields":
        old=x["Work"]["task-1"];new=y["Work"].get("task-1",{})
        keep=all(new.get(field)==old[field] for field in ("id","completed","due_date"))
        restold={k:v for k,v in x["Work"].items() if k!="task-1"};restnew={k:v for k,v in y["Work"].items() if k!="task-1"}
        return {"task1_renamed":new.get("title")=="Draft v2","protected_state_unchanged":keep and restold==restnew and x["Archive"]==y["Archive"]}
    if cid=="C05_clear_completed_only":
        active={key:value for key,value in x["Work"].items() if value.get("completed") is False}
        return {"completed_removed":all(value.get("completed") is False for value in w1),"active_and_archive_unchanged":y["Work"]==active and x["Archive"]==y["Archive"]}
    if cid=="C06_filter_is_view_only":
        views=row.get("views") or {};all_ids=set(x["Work"]);active_ids={key for key,value in x["Work"].items() if value.get("completed") is False}
        av=views.get("Active",[]);allv=views.get("All",[])
        return {"active_visible_exact":len(av)==len(set(av)) and set(av)==active_ids,"all_visible_exact":len(allv)==len(set(allv)) and set(allv)==all_ids,"records_unchanged":x==y}
    if cid=="C07_duplicate_title_id_target":
        altered=copy.deepcopy(y);target=altered["Work"].get("task-4")
        if target is not None:target["completed"]=x["Work"]["task-4"]["completed"]
        return {"only_task4_changed":y["Work"].get("task-4",{}).get("completed") is True and altered==x}
    if cid=="C08_missing_target_unknown":return {"unknown_target_no_change":row.get("status")=="UNKNOWN_TARGET" and x==y}
    raise ValueError(cid)

def path_exists(root,path):
    value=root
    for key in path.split("."):
        if not isinstance(value,dict) or key not in value:return False
        value=value[key]
    return True

problems=[];audited=[];rows=raw.get("rows",[])
if raw.get("coverage_obligations")!=len(matrix["obligations"]):problems.append("coverage-matrix cardinality mismatch")
for obligation in matrix["obligations"]:
    for row in rows:
        if row.get("case_id")==obligation["case"]:
            for path in obligation["raw_paths"]:
                if not path_exists(row,path):problems.append(f"raw evidence absent: {obligation['case']} {path}")
want=Counter([(cid,"baseline",None) for cid in byid]+[(cid,"ordinary_control",fault) for (cid,fault) in control_map])
got=Counter((row.get("case_id"),row.get("kind"),row.get("fault")) for row in rows)
if got!=want:problems.append("row/control inventory mismatch")
for row in rows:
    cid=row.get("case_id")
    if cid not in byid:problems.append(f"unknown case {cid}");continue
    truth=derive(row);failed={name for name,value in truth.items() if not value}
    if set(truth)!=clause_names[cid]:problems.append(f"clause inventory mismatch {cid}")
    if truth!=row.get("clause_results"):problems.append(f"candidate/auditor predicate mismatch {cid}/{row.get('fault')}")
    if row.get("accepted")!=all(truth.values()):problems.append(f"acceptance flag mismatch {cid}/{row.get('fault')}")
    if row.get("kind")=="baseline" and failed:problems.append(f"baseline failure {cid}:{sorted(failed)}")
    if row.get("kind")=="ordinary_control":
        key=(cid,row.get("fault"));expected=control_map.get(key)
        if expected is None or row.get("expected_failed_clause")!=expected or failed!={expected}:
            problems.append(f"control must fail only {expected}: {cid}/{row.get('fault')} -> {sorted(failed)}")
    audited.append({"case_id":cid,"kind":row.get("kind"),"fault":row.get("fault"),"failed":sorted(failed)})
print(json.dumps({"schema":"8088-a03-audit-v1","audit":"PASS" if not problems else "FAIL","rows":len(rows),"obligations":len(matrix["obligations"]),"controls_rejected":sum(r["kind"]=="ordinary_control" and bool(r["failed"]) for r in audited),"errors":problems,"audited":audited,"primary_cases":sorted(k for k in primary if k.startswith("C"))},sort_keys=True,separators=(",",":")))
sys.exit(bool(problems))
