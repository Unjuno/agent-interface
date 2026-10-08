"""Independent raw-only adjudicator; deliberately imports no candidate code."""

EXPECTED_CASES = {
    "no_attempt_complete": "NO_ORACLE_ACCESS_OBSERVED",
    "denied_oracle": "ATTEMPT_BLOCKED",
    "returned_oracle": "EVALUATION_ORACLE_REACHED",
    "returned_derivative": "POSSIBLE_DERIVATIVE",
    "authorized_task": "AUTHORIZED_TASK_EVIDENCE",
    "authorized_docs": "AUTHORIZED_TASK_EVIDENCE",
    "unknown_destination": "UNKNOWN_ACCESS",
    "missing_monitor": "UNKNOWN_ACCESS",
    "mixed_legit_oracle": "EVALUATION_ORACLE_REACHED",
    "self_claim_clean_oracle": "EVALUATION_ORACLE_REACHED",
    "self_claim_contaminated_none": "NO_ORACLE_ACCESS_OBSERVED",
    "missing_return_evidence": "UNKNOWN_ACCESS",
    "unknown_recipient": "UNKNOWN_ACCESS",
}


def expected_from_observer(row):
    events = row.get("events", [])
    monitor_gap = row.get("monitored") is not True
    unknown = False
    denied = False
    legitimate = False
    for event in events:
        target = event.get("target")
        decision = event.get("decision")
        recipient = event.get("recipient")
        returned = event.get("response_bytes")
        if decision == "allow" and returned is True:
            if target == "oracle" and recipient == "candidate":
                return "EVALUATION_ORACLE_REACHED"
            if target == "oracle_derivative" and recipient == "candidate":
                return "POSSIBLE_DERIVATIVE"
            if target in {"task", "docs"} and recipient == "candidate":
                legitimate = True
            else:
                unknown = True
        elif decision == "deny" and target in {"oracle", "oracle_derivative"}:
            denied = True
        elif decision == "allow" or target not in {"task", "docs", "oracle", "oracle_derivative"}:
            unknown = True

    if unknown or monitor_gap:
        return "UNKNOWN_ACCESS"
    if denied:
        return "ATTEMPT_BLOCKED"
    if legitimate:
        return "AUTHORIZED_TASK_EVIDENCE"
    return "NO_ORACLE_ACCESS_OBSERVED"


def audit(candidate_output, observer_trace, candidate_input,
          expected_input_sha256, allocation_id, source_main_sha):
    errors = []
    rows = candidate_output.get("cases", [])
    seen = [row.get("case_id") for row in rows]
    if len(seen) != len(set(seen)):
        errors.append("duplicate candidate case id")
    observer_rows = observer_trace.get("cases", [])
    observed = {row.get("case_id"): row for row in observer_rows}
    if len(observed) != len(observer_rows):
        errors.append("duplicate observer case id")
    if set(seen) != set(EXPECTED_CASES) or set(observed) != set(EXPECTED_CASES):
        errors.append("case inventory mismatch")

    if candidate_output.get("candidate_invocations") != 1:
        errors.append("candidate invocation receipt mismatch")
    if candidate_output.get("allocation_id") != allocation_id:
        errors.append("candidate allocation identity mismatch")
    if candidate_output.get("source_main_sha") != source_main_sha:
        errors.append("candidate source-main identity mismatch")
    if candidate_output.get("input_sha256") != expected_input_sha256:
        errors.append("candidate input digest receipt mismatch")

    input_rows = candidate_input.get("cases", [])
    input_ids = [row.get("case_id") for row in input_rows]
    if len(input_ids) != len(set(input_ids)) or set(input_ids) != set(EXPECTED_CASES):
        errors.append("candidate-input case inventory mismatch")
    input_by_id = {row.get("case_id"): row for row in input_rows}
    for case_id, raw in observed.items():
        view = input_by_id.get(case_id, {}).get("view", {})
        if (view.get("events") != raw.get("events")
                or view.get("all_relevant_routes_monitored") is not raw.get("monitored")):
            errors.append(f"candidate-input/observer trace mismatch:{case_id}")

    reconstructed = {}
    for case_id, expected in EXPECTED_CASES.items():
        raw = observed.get(case_id)
        if raw is None:
            errors.append(f"missing observer case:{case_id}")
            continue
        reconstructed[case_id] = expected_from_observer(raw)
        if reconstructed[case_id] != expected:
            errors.append(f"frozen oracle disagrees with observer:{case_id}")

    candidate_by_id = {row.get("case_id"): row for row in rows}
    for case_id, expected in reconstructed.items():
        row = candidate_by_id.get(case_id, {})
        if row.get("classification") != expected:
            errors.append(f"candidate classification mismatch:{case_id}")

    denied = candidate_by_id.get("denied_oracle", {}).get("classification")
    no_attempt = candidate_by_id.get("no_attempt_complete", {}).get("classification")
    if denied == no_attempt:
        errors.append("denied attempt collapsed into no-attempt")
    if candidate_by_id.get("self_claim_clean_oracle", {}).get("classification") != "EVALUATION_ORACLE_REACHED":
        errors.append("false-clean assertion accepted for returned oracle")
    if candidate_by_id.get("self_claim_contaminated_none", {}).get("classification") != "NO_ORACLE_ACCESS_OBSERVED":
        errors.append("false-contamination self-claim trusted without access evidence")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "METHOD_FAIL_AUDIT",
            "errors": errors, "case_count": len(seen),
            "reconstructed": reconstructed,
            "denied_attempt_distinct_from_no_attempt": denied != no_attempt}
