"""Deterministic candidate for the corrected Issue #6301 finite T0."""

import json
import sys


EFFECT_STATES = {"VERIFIED", "NOT_APPLIED_VERIFIED", "UNKNOWN"}
PENDING = {"PENDING", "UNKNOWN", "IN_PROGRESS"}


def score_task(task):
    effect = task["effect"]
    current = effect.get("receipt_generation") == task["generation"]
    effect_status = effect["state"] if current else "UNKNOWN"
    if effect_status not in EFFECT_STATES:
        raise ValueError(f"unsupported effect state: {effect_status}")

    obligations = sorted(
        [
            {"id": item["id"], "status": item["status"], "required": item["required"]}
            for item in task["obligations"]
        ],
        key=lambda item: item["id"],
    )
    pending_ids = sorted(
        item["id"] for item in obligations
        if item["required"] and item["status"] in PENDING
    )
    terminal = (
        "SUCCEEDED"
        if effect_status == "VERIFIED"
        and task["verification"] == "PASS"
        and task["release"] == "VERIFIED"
        and task["collateral"] == "CLEAR"
        and not pending_ids
        else "PENDING"
    )

    envelope = {
        "task_id": task["task"],
        "source_id": task["source"],
        "source_generation": task["generation"],
        "effect_status": effect_status,
        "obligations": obligations,
    }
    common = {
        "task_id": task["task"],
        "source_id": task["source"],
        "source_generation": task["generation"],
        "evidence_envelope": envelope,
    }
    if effect_status == "VERIFIED":
        generic_display = "Success"
        typed_display = "Effect verified; task status follows obligations"
    elif effect_status == "NOT_APPLIED_VERIFIED":
        generic_display = None
        typed_display = "No target effect verified; task status follows obligations"
    else:
        generic_display = None
        typed_display = "Effect status unknown; task remains unresolved"

    generic = {
        **common,
        "display": generic_display,
        "display_semantics": "UNSPECIFIED" if generic_display else "NONE",
        "availability": "EARLY",
    }
    typed = {
        **common,
        "display": typed_display,
        "display_semantics": "EFFECT_ONLY",
        "availability": "EARLY",
        "pending_obligation_ids": pending_ids,
    }
    late = (
        {
            **common,
            "display": "Task complete",
            "display_semantics": "TASK_TERMINAL",
            "availability": "TERMINAL",
        }
        if terminal == "SUCCEEDED"
        else {
            **common,
            "display": None,
            "display_semantics": "NONE",
            "availability": "WITHHELD_UNTIL_TERMINAL",
        }
    )
    evidence = {
        "task_id": task["task"],
        "source_id": task["source"],
        "source_generation": task["generation"],
        "effect_status": effect_status,
        "obligations": obligations,
        "task_terminal": terminal,
    }
    return {
        "evidence": evidence,
        "A_EARLY_GENERIC": generic,
        "B_TYPED_EFFECT_PENDING": typed,
        "C_LATE_TERMINAL_ONLY": late,
    }


def build_result(fixture):
    results = {}
    for trace in fixture["traces"]:
        tasks = trace.get("tasks", [trace])
        results[trace["id"]] = {
            task["task"]: score_task(task) for task in tasks
        }
    return {"schema": "6301-candidate-successor-v1", "results": results}


def main():
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    result = build_result(fixture)
    with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"candidate": "OK", "trace_count": len(result["results"])}))


if __name__ == "__main__":
    main()
