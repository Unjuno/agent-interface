"""Strict expected-inventory join for synthetic InputOwner release traces."""
from collections import Counter

BRACKET_EVENT = "owner_key_release_bracket"
TERMINAL_EVENT = "owner_release"
ALLOWED_OWNER_EVENTS = {BRACKET_EVENT, TERMINAL_EVENT}


def audit(trace, expected):
    errors = []
    if not isinstance(trace, dict):
        return ["trace_not_object"]
    if not isinstance(expected, dict):
        return ["expected_inventory_not_object"]
    owner_id = expected.get("owner_id")
    if not isinstance(owner_id, str) or not owner_id:
        errors.append("expected_owner_id_invalid")

    admissions_expected = expected.get("admissions")
    releases_expected = expected.get("releases")
    callers_expected = expected.get("caller_operations")
    terminals_expected = expected.get("terminals")
    if not isinstance(admissions_expected, list):
        return errors + ["expected_admissions_not_list"]
    if not isinstance(releases_expected, list):
        return errors + ["expected_releases_not_list"]
    if not isinstance(callers_expected, list):
        return errors + ["expected_caller_operations_not_list"]
    if not isinstance(terminals_expected, list):
        return errors + ["expected_terminals_not_list"]

    admissions = trace.get("admissions")
    caller_receipts = trace.get("caller_receipts")
    owner_records = trace.get("owner_records")
    for value, label in ((admissions, "admissions"), (caller_receipts, "caller_receipts"),
                         (owner_records, "owner_records")):
        if not isinstance(value, list):
            errors.append(f"{label}_not_list")
    if errors:
        return errors

    if len(admissions) != len(admissions_expected):
        errors.append("admission_count_mismatch")
    for i, (actual, planned) in enumerate(zip(admissions, admissions_expected)):
        if not isinstance(actual, dict) or not isinstance(planned, dict):
            errors.append(f"admission:{i}:not_object")
            continue
        receipt = actual.get("receipt")
        if actual.get("owner_id") != owner_id:
            errors.append(f"admission:{i}:owner_mismatch")
        if actual.get("intent_token") != planned.get("intent_token"):
            errors.append(f"admission:{i}:intent_mismatch")
        if actual.get("key") != planned.get("key") or actual.get("keycode") != planned.get("keycode"):
            errors.append(f"admission:{i}:key_identity_mismatch")
        if not isinstance(receipt, dict) or receipt.get("event") != "input_admission":
            errors.append(f"admission:{i}:receipt_invalid")
        elif receipt.get("key") != planned.get("key"):
            errors.append(f"admission:{i}:receipt_key_mismatch")
        elif (type(receipt.get("admitted_ns")) is not int
              or type(receipt.get("input_ack_ns")) is not int
              or receipt["admitted_ns"] > receipt["input_ack_ns"]):
            errors.append(f"admission:{i}:receipt_time_invalid")

    if len(caller_receipts) != len(callers_expected):
        errors.append("caller_count_mismatch")
    for i, (actual, planned) in enumerate(zip(caller_receipts, callers_expected)):
        if not isinstance(actual, dict) or not isinstance(planned, dict):
            errors.append(f"caller:{i}:not_object")
            continue
        if actual.get("owner_id") != owner_id:
            errors.append(f"caller:{i}:owner_mismatch")
        for name in ("operation", "intent_token", "key"):
            if actual.get(name) != planned.get(name):
                errors.append(f"caller:{i}:{name}_mismatch")
        start, finish = actual.get("started_ns"), actual.get("returned_ns")
        if type(start) is not int or type(finish) is not int or start > finish:
            errors.append(f"caller:{i}:time_invalid")
        if type(planned.get("expected_brackets")) is not int or planned["expected_brackets"] < 0:
            errors.append(f"caller:{i}:expected_bracket_count_invalid")

    brackets, terminals = [], []
    for i, row in enumerate(owner_records):
        if not isinstance(row, dict):
            errors.append(f"owner_record:{i}:not_object")
            continue
        event = row.get("event")
        if event == BRACKET_EVENT:
            brackets.append((i, row))
        elif event == TERMINAL_EVENT:
            terminals.append((i, row))
        else:
            errors.append(f"owner_record:{i}:unexpected_event")
    if len(brackets) != len(releases_expected):
        errors.append("release_bracket_count_mismatch")
    if len(terminals) != len(terminals_expected):
        errors.append("terminal_count_mismatch")

    admission_indices = []
    brackets_per_caller = Counter()
    for i, ((record_index, row), planned_release) in enumerate(zip(brackets, releases_expected)):
        if not isinstance(planned_release, dict):
            errors.append(f"release:{i}:expected_not_object")
            continue
        admission_index = planned_release.get("admission_index")
        caller_index = planned_release.get("caller_index")
        if type(admission_index) is not int or not 0 <= admission_index < len(admissions_expected):
            errors.append(f"release:{i}:admission_index_invalid")
            continue
        if type(caller_index) is not int or not 0 <= caller_index < len(caller_receipts):
            errors.append(f"release:{i}:caller_index_invalid")
            continue
        admission_indices.append(admission_index)
        admission = admissions_expected[admission_index]
        caller = caller_receipts[caller_index]
        brackets_per_caller[caller_index] += 1
        if row.get("schema") != "owner-key-release-bracket-v1":
            errors.append(f"release:{i}:schema")
        for name, wanted in (
            ("owner_id", owner_id),
            ("intent_token", admission.get("intent_token")),
            ("keycode", admission.get("keycode")),
            ("trigger_class", planned_release.get("trigger_class")),
            ("reason", planned_release.get("reason")),
        ):
            if row.get(name) != wanted:
                errors.append(f"release:{i}:{name}_mismatch")
        expected_raw_key = admission.get("key") if planned_release.get("trigger_class") == "explicit_up" else None
        if row.get("key") != expected_raw_key:
            errors.append(f"release:{i}:key_mismatch")
        required = ("request_started_ns", "request_returned_ns", "shared_sync_returned_ns",
                    "timing_valid", "grants_input_authority", "physical_key_up_claimed")
        if any(name not in row for name in required):
            errors.append(f"release:{i}:required_field_missing")
            continue
        a, b, c = (row.get(name) for name in
                   ("request_started_ns", "request_returned_ns", "shared_sync_returned_ns"))
        if any(type(x) is not int for x in (a, b, c)) or not a <= b <= c:
            errors.append(f"release:{i}:owner_time_invalid")
        if row.get("timing_valid") is not True:
            errors.append(f"release:{i}:timing_not_valid")
        if row.get("grants_input_authority") is not False:
            errors.append(f"release:{i}:authority_not_false")
        if row.get("physical_key_up_claimed") is not False:
            errors.append(f"release:{i}:physical_claim_not_false")
        if (caller.get("operation") != planned_release.get("caller_operation")
                or caller.get("intent_token") != admission.get("intent_token")):
            errors.append(f"release:{i}:caller_link_mismatch")
        start, finish = caller.get("started_ns"), caller.get("returned_ns")
        if (type(start) is int and type(finish) is int and type(a) is int
                and type(b) is int and type(c) is int
                and not start <= a <= b <= c <= finish):
            errors.append(f"release:{i}:caller_nesting_invalid")

    if sorted(admission_indices) != list(range(len(admissions_expected))):
        errors.append("admitted_key_release_coverage_mismatch")
    for i, planned in enumerate(callers_expected):
        if brackets_per_caller[i] != planned.get("expected_brackets"):
            errors.append(f"caller:{i}:bracket_count_mismatch")

    for i, ((record_index, row), planned) in enumerate(zip(terminals, terminals_expected)):
        if not isinstance(planned, dict):
            errors.append(f"terminal:{i}:expected_not_object")
            continue
        if row.get("reason") != planned.get("reason"):
            errors.append(f"terminal:{i}:reason_mismatch")
        if row.get("verified") is not True:
            errors.append(f"terminal:{i}:not_verified")
        if row.get("keys_down") != [] or row.get("buttons_down") != []:
            errors.append(f"terminal:{i}:not_neutral")
        if type(row.get("verified_ns")) is not int:
            errors.append(f"terminal:{i}:verified_time_invalid")

    return errors
