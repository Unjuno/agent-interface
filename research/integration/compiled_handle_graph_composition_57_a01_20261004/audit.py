import json
import sys
from pathlib import Path


def audit(candidate):
    if candidate.get("schema") != "compiled-handle-graph-composition-candidate-v1":
        raise ValueError("candidate schema mismatch")
    if candidate.get("source_main") != "41df296f3ce4d03c801c998d38f6e537e64a83ab":
        raise ValueError("candidate main pin mismatch")
    if candidate.get("case_count") != 5 or candidate.get("scenario_count") != 15:
        raise ValueError("expected five cases and fifteen scenarios")
    if (candidate.get("adapter_calls_are_test_doubles") is not True or
            candidate.get("live_gui_calls") != 0 or
            candidate.get("model_calls") != 0 or
            candidate.get("input_dispatch_calls") != 0):
        raise ValueError("scope fields mismatch")

    rows = candidate.get("rows")
    if type(rows) is not list or len(rows) != 15:
        raise ValueError("raw rows missing")
    expected = {(task, mode) for task in range(2, 7)
                for mode in ("baseline", "field_race", "submit_race")}
    if {(row.get("task"), row.get("mode")) for row in rows} != expected:
        raise ValueError("task/mode coverage mismatch")

    audited = []
    for row in rows:
        receipt = row.get("receipt")
        if type(receipt) is not dict or receipt.get("format") != "compiled-gui-runtime-receipt-v1":
            raise ValueError("runtime receipt missing")
        terminals = [e for e in receipt.get("critical_events", [])
                     if e.get("event") == "action_terminal"]
        refusals = [e for e in receipt.get("critical_events", [])
                    if e.get("event") == "admission_refused"]
        ops = row.get("execute_operations")
        mode = row["mode"]
        if mode == "baseline":
            passed = (receipt.get("outcome") == "TASK_SUCCEEDED" and
                      receipt.get("reason") == "method_complete" and
                      receipt.get("completed_transitions") == 2 and
                      ops == ["enter_exact_token", "activate_submit"] and
                      len(terminals) == 2 and not refusals)
        elif mode == "field_race":
            passed = (receipt.get("outcome") == "SAFE_YIELD" and
                      receipt.get("reason") == "missing_symbol" and
                      receipt.get("completed_transitions") == 0 and
                      ops == [] and len(refusals) == 1 and not terminals and
                      row.get("admission_checks", [{}])[0].get("pixel_resolution_status") == "MISSING")
        else:
            passed = (receipt.get("outcome") == "SAFE_YIELD" and
                      receipt.get("reason") == "missing_symbol" and
                      receipt.get("completed_transitions") == 1 and
                      ops == ["enter_exact_token"] and len(terminals) == 1 and
                      len(refusals) == 1 and
                      row.get("admission_checks", [{}, {}])[-1].get("pixel_resolution_status") == "MISSING")
        all_released = (len(terminals) == len(ops) and
                        all(event.get("release_verified") is True for event in terminals) and
                        row.get("release_verified_all_executions") is True)
        audited.append({"task": row["task"], "mode": mode,
                        "criteria_pass": bool(passed),
                        "all_test_double_executions_report_empty_release": all_released,
                        "runtime_outcome": receipt["outcome"],
                        "runtime_reason": receipt["reason"],
                        "operations": ops,
                        "admission_checks": row["admission_checks"]})
        if not passed or not all_released:
            raise ValueError(f"scenario failed independent audit: task={row['task']} mode={mode}")

    counts = {
        "baseline_two_action_success": sum(r["mode"] == "baseline" and r["criteria_pass"] for r in audited),
        "field_race_zero_action_refusal": sum(r["mode"] == "field_race" and r["criteria_pass"] for r in audited),
        "submit_race_entry_only_refusal": sum(r["mode"] == "submit_race" and r["criteria_pass"] for r in audited),
    }
    passed = counts == {
        "baseline_two_action_success": 5,
        "field_race_zero_action_refusal": 5,
        "submit_race_entry_only_refusal": 5,
    }
    return {"schema": "compiled-handle-graph-composition-audit-v1",
            "verdict": "PASS" if passed else "FAIL", "counts": counts,
            "audited_rows": audited,
            "scope": "offline test-double composition only; no live GUI, semantics, application effect, efficiency, or input-authority claim"}


if __name__ == "__main__":
    path = Path(sys.argv[1])
    result = audit(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2, sort_keys=True))
