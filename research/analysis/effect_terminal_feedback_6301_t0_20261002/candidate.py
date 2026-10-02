import json
import sys

PENDING = {"PENDING", "UNKNOWN", "IN_PROGRESS"}


def score_task(task):
    effect = task["effect"]
    current = effect.get("receipt_generation") == task["generation"]
    effect_status = effect["state"] if current else "UNKNOWN"
    open_ids = sorted(o["id"] for o in task["obligations"] if o["required"] and o["status"] in PENDING)
    success = (
        effect_status == "VERIFIED"
        and task["verification"] == "PASS"
        and task["release"] == "VERIFIED"
        and task["collateral"] == "CLEAR"
        and not open_ids
    )
    terminal = "SUCCEEDED" if success else "PENDING"
    evidence = {
        "task_id": task["task"],
        "source_id": task["source"],
        "source_generation": task["generation"],
        "effect_status": effect_status,
        "obligations": sorted(
            [{"id": o["id"], "status": o["status"], "required": o["required"]} for o in task["obligations"]],
            key=lambda o: o["id"],
        ),
        "task_terminal": terminal,
    }
    envelope = {
        "task_id": task["task"],
        "source_id": task["source"],
        "source_generation": task["generation"],
        "effect_status": effect_status,
        "obligations": evidence["obligations"],
    }
    common = {"task_id": task["task"], "source_id": task["source"], "source_generation": task["generation"], "evidence_envelope": envelope}
    if effect_status == "VERIFIED":
        generic = {**common, "display": "Success", "display_semantics": "UNSPECIFIED", "availability": "EARLY"}
        typed = {**common, "display": "Effect verified; task status follows obligations", "display_semantics": "EFFECT_ONLY", "availability": "EARLY", "pending_obligation_ids": open_ids}
    else:
        generic = {**common, "display": None, "display_semantics": "NONE", "availability": "EARLY"}
        typed = {**common, "display": "Effect not verified; task remains unresolved", "display_semantics": "EFFECT_ONLY", "availability": "EARLY", "pending_obligation_ids": open_ids}
    if terminal != "PENDING":
        late = {**common, "display": "Task complete", "display_semantics": "TASK_TERMINAL", "availability": "TERMINAL"}
    else:
        late = {**common, "display": None, "display_semantics": "NONE", "availability": "WITHHELD_UNTIL_TERMINAL"}
    return {"evidence": evidence, "A_EARLY_GENERIC": generic, "B_TYPED_EFFECT_PENDING": typed, "C_LATE_TERMINAL_ONLY": late}


def main():
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    results = {}
    for trace in fixture["traces"]:
        tasks = trace.get("tasks", [trace])
        results[trace["id"]] = {task["task"]: score_task(task) for task in tasks}
    print(json.dumps({"schema": "6301-candidate-v1", "results": results}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

