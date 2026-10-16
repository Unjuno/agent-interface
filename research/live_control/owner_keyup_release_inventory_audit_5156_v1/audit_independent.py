"""Independent raw-trace audit; does not import either candidate auditor."""
def audit(run, expected):
    errors = []
    if run.get("status") != "PASS_RELEASE_INVENTORY_AUDIT_CONSTRUCTION":
        errors.append("runner_status")
    if run.get("candidate_pristine_errors") != []:
        errors.append("candidate_pristine")
    suite = run.get("existing_owner_suite", {})
    if (suite.get("tests_run") != 14 or suite.get("failures") != 0
        or suite.get("errors") != 0):
        errors.append("existing_owner_suite")
    baseline = run.get("baseline_auditor", {})
    if set(baseline) != {"pristine", "empty", "all_brackets_omitted", "one_bracket_deleted"}:
        errors.append("baseline_control_set")
    elif any(baseline[k] != [] for k in baseline):
        errors.append("baseline_control_decisions")

    trace = run.get("trace")
    if not isinstance(trace, dict):
        return errors + ["trace_missing"]
    admissions = trace.get("admissions")
    callers = trace.get("caller_receipts")
    records = trace.get("owner_records")
    if not all(isinstance(x, list) for x in (admissions, callers, records)):
        return errors + ["trace_component_type"]

    if len(admissions) != len(expected["admissions"]):
        errors.append("admission_count")
    else:
        for got, want in zip(admissions, expected["admissions"]):
            receipt = got.get("receipt", {})
            if (got.get("owner_id") != expected["owner_id"]
                or got.get("intent_token") != want["intent_token"]
                or got.get("key") != want["key"]
                or got.get("keycode") != want["keycode"]
                or receipt.get("event") != "input_admission"
                or receipt.get("key") != want["key"]):
                errors.append("admission_identity")

    brackets = [r for r in records if isinstance(r, dict)
                and r.get("event") == "owner_key_release_bracket"]
    if len(brackets) != len(expected["releases"]):
        errors.append("bracket_count")
    else:
        for row, release in zip(brackets, expected["releases"]):
            aidx, cidx = release["admission_index"], release["caller_index"]
            admission = expected["admissions"][aidx]
            caller = callers[cidx]
            expected_key = admission["key"] if release["trigger_class"] == "explicit_up" else None
            vals = (row.get("owner_id"), row.get("intent_token"), row.get("keycode"),
                    row.get("key"), row.get("trigger_class"), row.get("reason"), row.get("schema"))
            want = (expected["owner_id"], admission["intent_token"], admission["keycode"],
                    expected_key, release["trigger_class"], release["reason"],
                    "owner-key-release-bracket-v1")
            if vals != want:
                errors.append("bracket_identity_or_order")
            ts = [row.get(n) for n in ("request_started_ns","request_returned_ns","shared_sync_returned_ns")]
            if any(type(x) is not int for x in ts) or not ts[0] <= ts[1] <= ts[2]:
                errors.append("owner_interval")
            if (type(caller.get("started_ns")) is not int
                or type(caller.get("returned_ns")) is not int
                or not caller["started_ns"] <= ts[0] <= ts[1] <= ts[2] <= caller["returned_ns"]):
                errors.append("caller_nesting")

    terminals = [r for r in records if isinstance(r, dict) and r.get("event") == "owner_release"]
    if len(terminals) != len(expected["terminals"]):
        errors.append("terminal_count")
    else:
        for row, want in zip(terminals, expected["terminals"]):
            if (row.get("reason") != want["reason"] or row.get("verified") is not True
                or row.get("keys_down") != [] or row.get("buttons_down") != []
                or type(row.get("verified_ns")) is not int):
                errors.append("terminal_not_empty_or_ordered")

    owner_behavior = run.get("owner_behavior", {})
    if not owner_behavior.get("v10_v11_behavior_equivalent"):
        errors.append("v10_v11_not_equivalent")
    if (owner_behavior.get("v10_sync_count") != owner_behavior.get("v11_sync_count")
        or owner_behavior.get("v11_final_keys_down") != []
        or owner_behavior.get("v10_final_keys_down") != []):
        errors.append("request_sync_or_neutral_state")

    mutations = run.get("candidate_mutation_results", {})
    expected_mutations = {"empty_trace", "all_brackets_omitted", "one_bracket_deleted",
                          "one_admission_deleted", "terminal_deleted", "keycode_tampered",
                          "timestamp_inverted"}
    if set(mutations) != expected_mutations:
        errors.append("mutation_control_set")
    elif any(not mutations[name] for name in expected_mutations):
        errors.append("candidate_failed_to_reject_mutation")

    return errors
