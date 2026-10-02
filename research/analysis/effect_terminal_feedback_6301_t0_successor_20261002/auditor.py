"""Independent raw-only oracle for the corrected Issue #6301 finite T0."""

import copy
import json
import sys


OPEN = {"PENDING", "UNKNOWN", "IN_PROGRESS"}
VALID_EFFECTS = {"VERIFIED", "NOT_APPLIED_VERIFIED", "UNKNOWN"}


def oracle_row(task):
    receipt_is_current = task["effect"].get("receipt_generation") == task["generation"]
    observed = task["effect"]["state"] if receipt_is_current else "UNKNOWN"
    if observed not in VALID_EFFECTS:
        raise ValueError("fixture contains unsupported effect state")
    obligations = sorted(
        [
            {"id": obligation["id"], "status": obligation["status"], "required": obligation["required"]}
            for obligation in task["obligations"]
        ],
        key=lambda obligation: obligation["id"],
    )
    unresolved = sorted(
        obligation["id"] for obligation in obligations
        if obligation["required"] and obligation["status"] in OPEN
    )
    is_terminal = (
        observed == "VERIFIED"
        and task["verification"] == "PASS"
        and task["release"] == "VERIFIED"
        and task["collateral"] == "CLEAR"
        and len(unresolved) == 0
    )
    terminal_label = "SUCCEEDED" if is_terminal else "PENDING"
    frame = {
        "task_id": task["task"],
        "source_id": task["source"],
        "source_generation": task["generation"],
        "effect_status": observed,
        "obligations": obligations,
    }
    identity = {
        "task_id": task["task"],
        "source_id": task["source"],
        "source_generation": task["generation"],
        "evidence_envelope": frame,
    }
    if observed == "VERIFIED":
        a_text, a_semantics = "Success", "UNSPECIFIED"
        b_text = "Effect verified; task status follows obligations"
    elif observed == "NOT_APPLIED_VERIFIED":
        a_text, a_semantics = None, "NONE"
        b_text = "No target effect verified; task status follows obligations"
    else:
        a_text, a_semantics = None, "NONE"
        b_text = "Effect status unknown; task remains unresolved"
    a = {**identity, "display": a_text, "display_semantics": a_semantics, "availability": "EARLY"}
    b = {
        **identity,
        "display": b_text,
        "display_semantics": "EFFECT_ONLY",
        "availability": "EARLY",
        "pending_obligation_ids": unresolved,
    }
    if is_terminal:
        c = {**identity, "display": "Task complete", "display_semantics": "TASK_TERMINAL", "availability": "TERMINAL"}
    else:
        c = {**identity, "display": None, "display_semantics": "NONE", "availability": "WITHHELD_UNTIL_TERMINAL"}
    evidence = {
        "task_id": task["task"],
        "source_id": task["source"],
        "source_generation": task["generation"],
        "effect_status": observed,
        "obligations": obligations,
        "task_terminal": terminal_label,
    }
    return {"evidence": evidence, "A_EARLY_GENERIC": a, "B_TYPED_EFFECT_PENDING": b, "C_LATE_TERMINAL_ONLY": c}


def reconstruct(fixture):
    traces = {}
    task_count = 0
    display_record_count = 0
    for trace in fixture["traces"]:
        per_task = {}
        for task in trace.get("tasks", [trace]):
            per_task[task["task"]] = oracle_row(task)
            task_count += 1
            display_record_count += 3
        traces[trace["id"]] = per_task
    return traces, task_count, display_record_count


def verify(fixture, candidate):
    expected, task_count, display_record_count = reconstruct(fixture)
    if candidate.get("schema") != "6301-candidate-successor-v1":
        raise AssertionError("candidate schema mismatch")
    if candidate.get("results") != expected:
        raise AssertionError("candidate rows differ from independent reconstruction")
    cancelled = candidate["results"]["cancelled_input"]["task-06"]
    if cancelled["evidence"]["effect_status"] != "NOT_APPLIED_VERIFIED":
        raise AssertionError("verified non-application was lost")
    if cancelled["B_TYPED_EFFECT_PENDING"]["display"] != "No target effect verified; task status follows obligations":
        raise AssertionError("verified non-application cue is inaccurate")
    if cancelled["evidence"]["task_terminal"] != "PENDING":
        raise AssertionError("pending release was improperly discharged")
    return task_count, display_record_count


def mutation_controls(fixture, candidate):
    controls = []
    edits = []

    dropped = copy.deepcopy(candidate)
    dropped["results"]["effect_before_release"]["task-01"]["B_TYPED_EFFECT_PENDING"]["pending_obligation_ids"] = []
    edits.append(("drop_pending_obligation", dropped))

    forged = copy.deepcopy(candidate)
    forged["results"]["effect_before_release"]["task-01"]["evidence"]["task_terminal"] = "SUCCEEDED"
    edits.append(("forge_terminal", forged))

    stale = copy.deepcopy(candidate)
    stale["results"]["stale_effect_generation"]["task-09"]["evidence"]["effect_status"] = "VERIFIED"
    edits.append(("promote_stale_effect", stale))

    accepted = copy.deepcopy(candidate)
    row = accepted["results"]["ambiguous_save"]["task-03"]
    row["evidence"]["effect_status"] = "VERIFIED"
    row["B_TYPED_EFFECT_PENDING"]["evidence_envelope"]["effect_status"] = "VERIFIED"
    row["B_TYPED_EFFECT_PENDING"]["display"] = "Effect verified; task status follows obligations"
    edits.append(("accepted_input_as_effect", accepted))

    for name, mutated in edits:
        try:
            verify(fixture, mutated)
        except (AssertionError, KeyError, TypeError, ValueError):
            controls.append({"mutation": name, "rejected": True})
        else:
            controls.append({"mutation": name, "rejected": False})
    return controls


def main():
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    candidate = json.load(open(sys.argv[2], encoding="utf-8"))
    task_count, display_record_count = verify(fixture, candidate)
    controls = mutation_controls(fixture, candidate)
    result = {
        "audit": "PASS_METHOD_SCOPED" if task_count == 10 and display_record_count == 30 and all(item["rejected"] for item in controls) else "FAIL_AUDIT",
        "task_count": task_count,
        "display_record_count": display_record_count,
        "mutations": controls,
        "errors": [],
    }
    if not all(item["rejected"] for item in controls):
        result["errors"] = ["one or more frozen mutation controls were accepted"]
    with open(sys.argv[3], "w", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps(result, sort_keys=True))
    if result["audit"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
