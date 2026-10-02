import json
import sys


def expected_task(trace, task):
    effect = task["effect"]
    effect_state = effect["state"] if effect.get("receipt_generation") == task["generation"] else "UNKNOWN"
    obligations = sorted(
        [{"id": x["id"], "status": x["status"], "required": x["required"]} for x in task["obligations"]],
        key=lambda x: x["id"],
    )
    pending = sorted(x["id"] for x in obligations if x["required"] and x["status"] in ("PENDING", "UNKNOWN", "IN_PROGRESS"))
    terminal = "SUCCEEDED" if (
        effect_state == "VERIFIED" and task["verification"] == "PASS"
        and task["release"] == "VERIFIED" and task["collateral"] == "CLEAR" and not pending
    ) else "PENDING"
    envelope = {"task_id": task["task"], "source_id": task["source"], "source_generation": task["generation"], "effect_status": effect_state, "obligations": obligations}
    ids = {"task_id": task["task"], "source_id": task["source"], "source_generation": task["generation"], "evidence_envelope": envelope}
    evidence = {**ids, "effect_status": effect_state, "obligations": obligations, "task_terminal": terminal}
    if effect_state == "VERIFIED":
        generic = {**ids, "display": "Success", "display_semantics": "UNSPECIFIED", "availability": "EARLY"}
        typed = {**ids, "display": "Effect verified; task status follows obligations", "display_semantics": "EFFECT_ONLY", "availability": "EARLY", "pending_obligation_ids": pending}
    else:
        generic = {**ids, "display": None, "display_semantics": "NONE", "availability": "EARLY"}
        typed = {**ids, "display": "Effect not verified; task remains unresolved", "display_semantics": "EFFECT_ONLY", "availability": "EARLY", "pending_obligation_ids": pending}
    if terminal != "PENDING":
        late = {**ids, "display": "Task complete", "display_semantics": "TASK_TERMINAL", "availability": "TERMINAL"}
    else:
        late = {**ids, "display": None, "display_semantics": "NONE", "availability": "WITHHELD_UNTIL_TERMINAL"}
    return {"evidence": evidence, "A_EARLY_GENERIC": generic, "B_TYPED_EFFECT_PENDING": typed, "C_LATE_TERMINAL_ONLY": late}


def verify(fixture, raw):
    wanted = {}
    for trace in fixture["traces"]:
        wanted[trace["id"]] = {task["task"]: expected_task(trace, task) for task in trace.get("tasks", [trace])}
    assert raw["results"] == wanted, "candidate output differs from independent reconstruction"
    for trace_id, task_rows in raw["results"].items():
        for task_id, row in task_rows.items():
            evidence = row["evidence"]
            assert row["A_EARLY_GENERIC"]["task_id"] == task_id
            assert row["B_TYPED_EFFECT_PENDING"]["task_id"] == task_id
            assert evidence["task_terminal"] == "PENDING" or evidence["task_terminal"] == "SUCCEEDED"
            if evidence["task_terminal"] == "PENDING":
                assert row["C_LATE_TERMINAL_ONLY"]["display"] is None
            assert evidence["task_id"] == task_id
            for display in ("A_EARLY_GENERIC", "B_TYPED_EFFECT_PENDING", "C_LATE_TERMINAL_ONLY"):
                assert row[display] is None or row[display]["evidence_envelope"] == {
                    "task_id": task_id,
                    "source_id": evidence["source_id"],
                    "source_generation": evidence["source_generation"],
                    "effect_status": evidence["effect_status"],
                    "obligations": evidence["obligations"],
                }
    return sum(len(rows) for rows in raw["results"].values())


def rejected(fixture, candidate_raw, mutation):
    try:
        verify(fixture, mutation)
    except (AssertionError, KeyError, TypeError):
        return True
    return False


def main():
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    raw = json.load(open(sys.argv[2], encoding="utf-8"))
    task_rows = verify(fixture, raw)
    samples = []
    dropped = json.loads(json.dumps(raw)); dropped["results"]["effect_before_release"]["task-01"]["B_TYPED_EFFECT_PENDING"]["pending_obligation_ids"] = []
    samples.append(rejected(fixture, raw, dropped))
    forged = json.loads(json.dumps(raw)); forged["results"]["effect_before_release"]["task-01"]["evidence"]["task_terminal"] = "SUCCEEDED"
    samples.append(rejected(fixture, raw, forged))
    stale = json.loads(json.dumps(raw)); stale["results"]["stale_effect_generation"]["task-09"]["evidence"]["effect_status"] = "VERIFIED"
    samples.append(rejected(fixture, raw, stale))
    accepted = json.loads(json.dumps(raw)); accepted["results"]["ambiguous_save"]["task-03"]["evidence"]["effect_status"] = "VERIFIED"
    samples.append(rejected(fixture, raw, accepted))
    assert len(samples) == 4 and all(samples)
    print(json.dumps({"schema": "6301-audit-v1", "trace_task_rows": task_rows, "display_rows": task_rows * 3, "errors": 0, "mutations_rejected": sum(samples), "premature_terminal_successes": 0}, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

