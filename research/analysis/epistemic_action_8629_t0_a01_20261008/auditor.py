def _need_from_observation(task_input):
    evidence = task_input["evidence"]
    if not evidence["decision_set"]:
        return "UNKNOWN"
    if evidence["complete"] and evidence["representation_usable"] and len(evidence["decision_set"]) == 1:
        return "SUFFICIENT"
    if not evidence["complete"] and "ACQUIRE" in task_input["safe_actions"]:
        return "NEEDS_ACQUISITION"
    if evidence["complete"] and not evidence["representation_usable"] and "TRANSFORM" in task_input["safe_actions"]:
        return "NEEDS_TRANSFORM"
    if not evidence["complete"] and "PROBE" in task_input["safe_actions"]:
        return "NEEDS_PROBE"
    return "BLOCKED_EVIDENCE"


def _truth_from_observation(task_input):
    need = _need_from_observation(task_input)
    expected = {
        "NEEDS_ACQUISITION": "ACQUIRE",
        "NEEDS_TRANSFORM": "TRANSFORM",
        "NEEDS_PROBE": "PROBE",
        "SUFFICIENT": "COMMIT",
        "BLOCKED_EVIDENCE": "YIELD",
        "UNKNOWN": "YIELD",
    }[need]
    if expected in {"ACQUIRE", "TRANSFORM", "PROBE"}:
        response = task_input["action_responses"].get(expected)
        if not response or not response["safe"]:
            return need, "YIELD", "UNKNOWN"
        evidence = response["evidence"]
    else:
        evidence = task_input["evidence"]
    decision = evidence["decision_set"][0] if evidence["complete"] and evidence["representation_usable"] and len(evidence["decision_set"]) == 1 else "UNKNOWN"
    return need, expected, decision


def _reference_action(task_input, policy, arm):
    allowed = set(task_input["allowed_actions"])
    if arm == "NO_EPISTEMIC_ACTION":
        allowed.intersection_update({"COMMIT", "YIELD"})
    evidence = task_input["evidence"]
    if not evidence["decision_set"]:
        return "YIELD"
    if evidence["complete"] and evidence["representation_usable"] and len(evidence["decision_set"]) == 1:
        if policy == "STOPPING_DEFECT" and "PROBE" in allowed and "PROBE" in task_input["safe_actions"]:
            return "PROBE"
        return "COMMIT" if "COMMIT" in allowed else "YIELD"
    for action in ("ACQUIRE", "TRANSFORM", "PROBE"):
        if action in allowed and action in task_input["safe_actions"]:
            return "YIELD" if policy == "ACTION_SELECTION_DEFECT" and arm == "AVAILABLE" else action
    return "YIELD"


def _expected_row(case, oracle_truth, policy, arm):
    task_input = case["input"]
    need, correct_action, correct_decision = _truth_from_observation(task_input)
    if oracle_truth != {"decision": correct_decision, "epistemic_action": correct_action, "need": need}:
        raise ValueError("oracle label mismatch for " + case["case_id"])

    if arm == "PRESCRIBED":
        action = case["prescription"] if case["prescription"] in task_input["allowed_actions"] else "YIELD"
    else:
        action = _reference_action(task_input, policy, arm)

    before = task_input["evidence"]
    response = task_input["action_responses"].get(action)
    after = response["evidence"] if action in {"ACQUIRE", "TRANSFORM", "PROBE"} and response and response["safe"] else before
    if policy == "EVIDENCE_USE_DEFECT" and after != before and action in {"ACQUIRE", "TRANSFORM", "PROBE"}:
        decision = "UNKNOWN"
    elif action == "COMMIT" and before["complete"] and before["representation_usable"] and len(before["decision_set"]) == 1:
        decision = before["decision_set"][0]
    elif after["complete"] and after["representation_usable"] and len(after["decision_set"]) == 1:
        decision = after["decision_set"][0]
    else:
        decision = "UNKNOWN"
    recognized = "UNKNOWN" if policy == "RECOGNITION_DEFECT" else need
    unnecessary = action in {"ACQUIRE", "TRANSFORM", "PROBE"} and before == after
    violation = action in {"ACQUIRE", "TRANSFORM", "PROBE"} and action not in task_input["safe_actions"]
    return {
        "case_id": case["case_id"], "policy": policy, "arm": arm,
        "recognized_need": recognized, "selected_action": action,
        "evidence_before": before, "evidence_after": after,
        "action_response": response, "final_decision": decision,
        "unnecessary_action": unnecessary, "hard_gate_violation": violation,
    }


def _audit_core(fixture, oracle, raw):
    errors = []
    if raw.get("schema") != "epistemic-action-8629-candidate-v1":
        errors.append("candidate schema mismatch")
    case_by_id = {case["case_id"]: case for case in fixture.get("cases", [])}
    oracle_by_id = oracle.get("cases", {})
    if len(case_by_id) != len(fixture.get("cases", [])) or set(case_by_id) != set(oracle_by_id):
        errors.append("fixture/oracle case identity mismatch")

    policies = ("REFERENCE", "RECOGNITION_DEFECT", "ACTION_SELECTION_DEFECT", "EVIDENCE_USE_DEFECT", "STOPPING_DEFECT")
    arms = ("PRESCRIBED", "AVAILABLE", "NO_EPISTEMIC_ACTION")
    wanted = {(cid, policy, arm) for cid in case_by_id for policy in policies for arm in arms}
    observed = set()
    metrics = {}
    rows = raw.get("rows", [])
    for row in rows:
        key = (row.get("case_id"), row.get("policy"), row.get("arm"))
        if key in observed:
            errors.append("duplicate row " + repr(key))
            continue
        observed.add(key)
        if key not in wanted:
            errors.append("unexpected row " + repr(key))
            continue
        cid, policy, arm = key
        try:
            expected = _expected_row(case_by_id[cid], oracle_by_id[cid], policy, arm)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append("cannot reconstruct " + repr(key) + ": " + str(exc))
            continue
        if row != expected:
            errors.append("row differs from independent reconstruction " + repr(key))
        bucket = metrics.setdefault(policy + "/" + arm, {
            "denominator": len(case_by_id), "recognition_correct": 0,
            "action_selection_correct": 0, "evidence_production_correct": 0,
            "evidence_production_denominator": 0, "evidence_use_correct": 0,
            "evidence_use_denominator": 0, "stopping_correct": 0,
            "task_success": 0, "hard_gate_violations": 0,
            "unnecessary_actions": 0,
        })
        truth = oracle_by_id[cid]
        bucket["recognition_correct"] += int(row.get("recognized_need") == truth["need"])
        bucket["action_selection_correct"] += int(row.get("selected_action") == truth["epistemic_action"])
        if truth["need"] in {"NEEDS_ACQUISITION", "NEEDS_TRANSFORM", "NEEDS_PROBE"}:
            bucket["evidence_production_denominator"] += 1
            produced = row.get("selected_action") == truth["epistemic_action"] and row.get("evidence_after") != row.get("evidence_before") and not row.get("hard_gate_violation")
            bucket["evidence_production_correct"] += int(produced)
            bucket["evidence_use_denominator"] += 1
            bucket["evidence_use_correct"] += int(row.get("final_decision") == truth["decision"])
        stop_ok = row.get("selected_action") in {"COMMIT", "YIELD"} if truth["need"] in {"SUFFICIENT", "BLOCKED_EVIDENCE", "UNKNOWN"} else row.get("selected_action") == truth["epistemic_action"]
        bucket["stopping_correct"] += int(stop_ok)
        bucket["task_success"] += int(row.get("final_decision") == truth["decision"])
        bucket["hard_gate_violations"] += int(bool(row.get("hard_gate_violation")))
        bucket["unnecessary_actions"] += int(bool(row.get("unnecessary_action")))

    if observed != wanted:
        errors.append("row coverage mismatch: expected " + str(len(wanted)) + " unique rows, got " + str(len(observed)))
    return {"errors": errors, "rows_reconstructed": len(observed & wanted), "rows_expected": len(wanted), "metrics": metrics}


def audit(fixture, oracle, raw):
    result = _audit_core(fixture, oracle, raw)
    controls = []
    cases = raw.get("rows", [])
    if cases:
        from copy import deepcopy
        mutations = []
        missing = deepcopy(raw); missing["rows"].pop(); mutations.append(missing)
        bad_action = deepcopy(raw); bad_action["rows"][0]["selected_action"] = "YIELD"; mutations.append(bad_action)
        bad_provenance = deepcopy(raw); bad_provenance["rows"][0]["evidence_after"]["provenance"].append("fabricated"); mutations.append(bad_provenance)
        bad_decision = deepcopy(raw); bad_decision["rows"][0]["final_decision"] = "DENY"; mutations.append(bad_decision)
    controls = [_audit_core(fixture, oracle, item)["errors"] for item in mutations]
    rejected = sum(bool(errors) for errors in controls)
    metrics = result["metrics"]
    reference = metrics.get("REFERENCE/AVAILABLE", {})
    recognize_fault = metrics.get("RECOGNITION_DEFECT/AVAILABLE", {})
    select_fault = metrics.get("ACTION_SELECTION_DEFECT/AVAILABLE", {})
    use_fault = metrics.get("EVIDENCE_USE_DEFECT/AVAILABLE", {})
    stop_fault = metrics.get("STOPPING_DEFECT/AVAILABLE", {})
    hypothesis_gates = {
        "recognition_defect_detected": recognize_fault.get("recognition_correct", 0) < reference.get("recognition_correct", -1),
        "selection_defect_detected": select_fault.get("action_selection_correct", 0) < reference.get("action_selection_correct", -1),
        "evidence_use_defect_detected": use_fault.get("evidence_use_correct", 0) < reference.get("evidence_use_correct", -1) and use_fault.get("evidence_production_correct", 0) == reference.get("evidence_production_correct", -1),
        "stopping_defect_hidden_by_task_success": stop_fault.get("task_success", -1) == reference.get("task_success", -2) and stop_fault.get("stopping_correct", -1) < reference.get("stopping_correct", -2) and stop_fault.get("unnecessary_actions", 0) > 0,
        "zero_hard_gate_violations": all(bucket.get("hard_gate_violations", 1) == 0 for bucket in metrics.values()),
    }
    method_ok = not result["errors"] and result["rows_reconstructed"] == result["rows_expected"] and rejected == 4
    hypothesis_ok = method_ok and all(hypothesis_gates.values())
    return {
        "schema": "epistemic-action-8629-audit-v1",
        "method_disposition": "PASS_METHOD_SCOPED" if method_ok else "FAIL_METHOD",
        "hypothesis_disposition": "H_PASS_SCOPED" if hypothesis_ok else ("H_FAIL_SCOPED" if method_ok else "HOLD"),
        "rows_reconstructed": result["rows_reconstructed"],
        "rows_expected": result["rows_expected"],
        "errors": result["errors"],
        "metrics": result["metrics"],
        "hypothesis_gates": hypothesis_gates,
        "mutation_controls_rejected": rejected,
        "mutation_controls_total": len(controls),
    }


def main():
    import argparse
    import json
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--oracle", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    oracle = json.loads(Path(args.oracle).read_text(encoding="utf-8"))
    raw = json.load(sys.stdin)
    result = audit(fixture, oracle, raw)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["method_disposition"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
