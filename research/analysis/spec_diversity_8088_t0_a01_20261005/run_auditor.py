"""Independent raw-output auditor; deliberately does not import candidate code."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
raw = json.loads(Path(sys.argv[1]).read_text())
packet = json.loads((HERE / "CONTRACTS.json").read_text())
spec_a = json.loads((HERE / "SPEC_A_PRIMARY.json").read_text())
source = {c["id"]: c for c in packet["contracts"]}
expected_names = {
 "C01_add_work_persists_once":{"work_plan_launch_count_1","preexisting_state_unchanged"},
 "C02_add_archive_only":{"archive_pack_kit_count_1","work_pack_kit_count_0","preexisting_state_unchanged"},
 "C03_complete_one_id":{"task2_complete_after_reload","task2_other_fields_unchanged","other_items_and_archive_unchanged"},
 "C04_rename_preserves_fields":{"task1_renamed_after_reload","task1_id_completion_due_date_preserved","other_items_and_lists_unchanged"},
 "C05_clear_completed_only":{"completed_work_removed_after_reload","active_work_unchanged","archive_unchanged"},
 "C06_filter_is_view_only":{"active_filter_exact","records_counts_archive_unchanged","all_filter_restores_all"},
 "C07_duplicate_title_id_target":{"task4_complete_only","task2_and_other_fields_unchanged"},
 "C08_missing_target_unknown":{"unknown_target","no_state_change","no_guess_or_success"}}

def predicates(row):
    cid, before, after = row["case_id"], row["initial"], row["final"]
    bw, ba, aw, aa = before["Work"], before["Archive"], after["Work"], after["Archive"]
    status = row["status"]
    if cid == "C01_add_work_persists_once":
        return {"work_plan_launch_count_1":sum(x.get("title")=="Plan launch" for x in aw)==1,
                "preexisting_state_unchanged":all(x in aw for x in bw) and all(x in aa for x in ba)}
    if cid == "C02_add_archive_only":
        return {"archive_pack_kit_count_1":sum(x.get("title")=="Pack kit" for x in aa)==1,
                "work_pack_kit_count_0":sum(x.get("title")=="Pack kit" for x in aw)==0,
                "preexisting_state_unchanged":all(x in aw for x in bw) and all(x in aa for x in ba)}
    if cid == "C03_complete_one_id":
        old=next(x for x in bw if x["id"]=="task-2"); new=next((x for x in aw if x.get("id")=="task-2"),{})
        return {"task2_complete_after_reload":new.get("completed") is True,
                "task2_other_fields_unchanged":{k:v for k,v in old.items() if k!="completed"}=={k:v for k,v in new.items() if k!="completed"},
                "other_items_and_archive_unchanged":[x for x in aw if x.get("id")!="task-2"]==[x for x in bw if x["id"]!="task-2"] and aa==ba}
    if cid == "C04_rename_preserves_fields":
        old=next(x for x in bw if x["id"]=="task-1"); new=next((x for x in aw if x.get("id")=="task-1"),{})
        return {"task1_renamed_after_reload":new.get("title")=="Draft v2",
                "task1_id_completion_due_date_preserved":all(new.get(k)==old[k] for k in ("id","completed","due_date")),
                "other_items_and_lists_unchanged":[x for x in aw if x.get("id")!="task-1"]==[x for x in bw if x["id"]!="task-1"] and aa==ba}
    if cid == "C05_clear_completed_only":
        active=[x for x in bw if not x["completed"]]
        return {"completed_work_removed_after_reload":not any(x.get("completed") for x in aw),
                "active_work_unchanged":all(x in aw for x in active),"archive_unchanged":aa==ba}
    if cid == "C06_filter_is_view_only":
        ids={x["id"] for x in bw if not x["completed"]}
        return {"active_filter_exact":set(row.get("visible") or [])==ids,"records_counts_archive_unchanged":aw==bw and aa==ba,
                "all_filter_restores_all":{x["id"] for x in aw}=={x["id"] for x in bw}}
    if cid == "C07_duplicate_title_id_target":
        return {"task4_complete_only":next((x.get("completed") for x in aw if x.get("id")=="task-4"),False) is True,
                "task2_and_other_fields_unchanged":next((x for x in aw if x.get("id")=="task-2"),None)==next((x for x in bw if x["id"]=="task-2"),None) and all(x in aw for x in bw if x["id"] not in ("task-4","task-2"))}
    if cid == "C08_missing_target_unknown":
        return {"unknown_target":status=="UNKNOWN_TARGET","no_state_change":after==before,
                "no_guess_or_success":status!="SUCCESS" and after==before}
    raise ValueError(cid)

problems=[]
seen=[]
for row in raw["rows"]:
    cid=row["case_id"]
    if cid not in source or cid not in expected_names: problems.append(f"unknown contract: {cid}"); continue
    if row["clauses"] != sorted(row["clauses"]):
        # Candidate order need not be canonical; this is not a semantic discrepancy.
        pass
    if set(row["clause_results"]) != expected_names[cid]: problems.append(f"clause inventory mismatch: {cid}")
    recomputed=predicates(row)
    if recomputed != row["clause_results"]: problems.append(f"predicate mismatch: {cid}/{row['kind']}")
    if row["accepted"] != all(recomputed.values()): problems.append(f"acceptance mismatch: {cid}/{row['kind']}")
    seen.append((cid,row["kind"],row["accepted"]))
if len(seen)!=12 or sum(k=="baseline" for _,k,_ in seen)!=8 or sum(k=="ordinary_control" for _,k,_ in seen)!=4:
    problems.append("expected exactly 8 baselines and 4 ordinary controls")
if any(not ok for _,kind,ok in seen if kind=="baseline"):
    problems.append("one or more baseline cases were rejected")
if any(ok for _,kind,ok in seen if kind=="ordinary_control"):
    problems.append("one or more ordinary controls survived")
print(json.dumps({"schema":"8088-independent-audit-v1","rows_audited":len(seen),"problems":problems,"audit":"PASS" if not problems else "FAIL","ordinary_controls_rejected":sum(not ok for _,k,ok in seen if k=="ordinary_control"),"primary_spec_cases":sorted(k for k in spec_a if k.startswith("C")),"candidate_rows":len(raw.get("rows",[]))},sort_keys=True,separators=(",",":")))
sys.exit(bool(problems))
