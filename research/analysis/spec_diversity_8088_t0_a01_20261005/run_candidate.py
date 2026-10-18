"""Deterministic candidate/scorer for the frozen synthetic #8088 packet."""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
contracts = json.loads((HERE / "CONTRACTS.json").read_text())
spec = json.loads((HERE / "SPEC_A_PRIMARY.json").read_text())


def clauses(contract):
    """Primary-only clause inventory, independently translated to predicates."""
    cid = contract["id"]
    req = contract["request"]
    if cid == "C01_add_work_persists_once":
        return ["work_plan_launch_count_1", "preexisting_state_unchanged"]
    if cid == "C02_add_archive_only":
        return ["archive_pack_kit_count_1", "work_pack_kit_count_0", "preexisting_state_unchanged"]
    if cid == "C03_complete_one_id":
        return ["task2_complete_after_reload", "task2_other_fields_unchanged", "other_items_and_archive_unchanged"]
    if cid == "C04_rename_preserves_fields":
        return ["task1_renamed_after_reload", "task1_id_completion_due_date_preserved", "other_items_and_lists_unchanged"]
    if cid == "C05_clear_completed_only":
        return ["completed_work_removed_after_reload", "active_work_unchanged", "archive_unchanged"]
    if cid == "C06_filter_is_view_only":
        return ["active_filter_exact", "records_counts_archive_unchanged", "all_filter_restores_all"]
    if cid == "C07_duplicate_title_id_target":
        return ["task4_complete_only", "task2_and_other_fields_unchanged"]
    if cid == "C08_missing_target_unknown":
        return ["unknown_target", "no_state_change", "no_guess_or_success"]
    raise ValueError(cid)


def check(cid, initial, final, status, visible=None):
    """Score contract clauses without importing an implementation oracle."""
    ok = {}
    w0, a0 = initial["Work"], initial["Archive"]
    w1, a1 = final["Work"], final["Archive"]
    if cid == "C01_add_work_persists_once":
        ok = {"work_plan_launch_count_1": sum(x["title"] == "Plan launch" for x in w1) == 1,
              "preexisting_state_unchanged": all(x in w1 for x in w0) and all(x in a1 for x in a0)}
    elif cid == "C02_add_archive_only":
        ok = {"archive_pack_kit_count_1": sum(x["title"] == "Pack kit" for x in a1) == 1,
              "work_pack_kit_count_0": sum(x["title"] == "Pack kit" for x in w1) == 0,
              "preexisting_state_unchanged": all(x in w1 for x in w0) and all(x in a1 for x in a0)}
    elif cid == "C03_complete_one_id":
        before = next(x for x in w0 if x["id"] == "task-2")
        after = next((x for x in w1 if x["id"] == "task-2"), {})
        ok = {"task2_complete_after_reload": after.get("completed") is True,
              "task2_other_fields_unchanged": {k:v for k,v in before.items() if k != "completed"} == {k:v for k,v in after.items() if k != "completed"},
              "other_items_and_archive_unchanged": [x for x in w1 if x.get("id") != "task-2"] == [x for x in w0 if x["id"] != "task-2"] and a1 == a0}
    elif cid == "C04_rename_preserves_fields":
        before = next(x for x in w0 if x["id"] == "task-1")
        after = next((x for x in w1 if x.get("id") == "task-1"), {})
        ok = {"task1_renamed_after_reload": after.get("title") == "Draft v2",
              "task1_id_completion_due_date_preserved": all(after.get(k) == before[k] for k in ("id", "completed", "due_date")),
              "other_items_and_lists_unchanged": [x for x in w1 if x.get("id") != "task-1"] == [x for x in w0 if x["id"] != "task-1"] and a1 == a0}
    elif cid == "C05_clear_completed_only":
        active = [x for x in w0 if not x["completed"]]
        ok = {"completed_work_removed_after_reload": not any(x["completed"] for x in w1),
              "active_work_unchanged": all(x in w1 for x in active), "archive_unchanged": a1 == a0}
    elif cid == "C06_filter_is_view_only":
        active = {x["id"] for x in w0 if not x["completed"]}
        ok = {"active_filter_exact": set(visible or []) == active,
              "records_counts_archive_unchanged": w1 == w0 and a1 == a0,
              "all_filter_restores_all": set(x["id"] for x in w1) == set(x["id"] for x in w0)}
    elif cid == "C07_duplicate_title_id_target":
        ok = {"task4_complete_only": next((x.get("completed") for x in w1 if x.get("id") == "task-4"), False) is True,
              "task2_and_other_fields_unchanged": next((x for x in w1 if x.get("id") == "task-2"), None) == next((x for x in w0 if x["id"] == "task-2"), None) and all(x in w1 for x in w0 if x["id"] not in ("task-4", "task-2"))}
    elif cid == "C08_missing_target_unknown":
        ok = {"unknown_target": status == "UNKNOWN_TARGET", "no_state_change": final == initial,
              "no_guess_or_success": status != "SUCCESS" and final == initial}
    return ok


def transition(cid, initial, mutant=None):
    state = copy.deepcopy(initial)
    status, visible = "SUCCESS", None
    if cid == "C01_add_work_persists_once":
        state["Work"].append({"id":"new-1","title":"Plan launch","completed":False,"due_date":None})
        if mutant == "persistence_lost": state["Work"] = copy.deepcopy(initial["Work"])
    elif cid == "C02_add_archive_only":
        row = {"id":"new-1","title":"Pack kit","completed":False,"due_date":None}
        state["Work" if mutant == "wrong_destination" else "Archive"].append(row)
    elif cid == "C03_complete_one_id":
        next(x for x in state["Work"] if x["id"] == "task-2")["completed"] = True
        if mutant == "forbidden_side_effect": next(x for x in state["Work"] if x["id"] == "task-1")["title"] = "CORRUPTED"
    elif cid == "C04_rename_preserves_fields": next(x for x in state["Work"] if x["id"] == "task-1")["title"] = "Draft v2"
    elif cid == "C05_clear_completed_only": state["Work"] = [x for x in state["Work"] if not x["completed"]]
    elif cid == "C06_filter_is_view_only":
        visible = [x["id"] for x in state["Work"] if not x["completed"]]
    elif cid == "C07_duplicate_title_id_target": next(x for x in state["Work"] if x["id"] == "task-4")["completed"] = True
    elif cid == "C08_missing_target_unknown":
        status = "SUCCESS" if mutant == "wrong_unknown" else "UNKNOWN_TARGET"
        if mutant == "wrong_unknown": next(x for x in state["Work"] if x["id"] == "task-2")["completed"] = True
    return state, status, visible


faults = [("C01_add_work_persists_once", "persistence_lost"),
          ("C02_add_archive_only", "wrong_destination"),
          ("C03_complete_one_id", "forbidden_side_effect"),
          ("C08_missing_target_unknown", "wrong_unknown")]
rows = []
by_id = {x["id"]: x for x in contracts["contracts"]}
for cid in by_id:
    initial = by_id[cid]["initial"]
    state, status, visible = transition(cid, initial)
    baseline = check(cid, initial, state, status, visible)
    rows.append({"case_id":cid,"kind":"baseline","initial":initial,"final":state,"status":status,"visible":visible,"clauses":clauses(by_id[cid]),"clause_results":baseline,"accepted":all(baseline.values())})
for cid, mutant in faults:
    initial = by_id[cid]["initial"]
    state, status, visible = transition(cid, initial, mutant)
    results = check(cid, initial, state, status, visible)
    rows.append({"case_id":cid,"kind":"ordinary_control","mutant":mutant,"initial":initial,"final":state,"status":status,"visible":visible,"clauses":clauses(by_id[cid]),"clause_results":results,"accepted":all(results.values())})
output = {"schema":"8088-candidate-output-v1","rows":rows}
print(json.dumps(output,sort_keys=True,separators=(",",":")))
