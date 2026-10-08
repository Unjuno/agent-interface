"""Independent postcondition oracle. Does not import predecessor runtime/audit."""
from copy import deepcopy

TARGET_TO_FIELD = {"toggle_email_reminders": "email_reminders"}
INTENT_TO_FIELD = {
    "enable_email_reminders": "email_reminders",
    "set_digest_frequency": "digest_frequency",
    "set_timezone": "timezone",
    "set_display_name": "display_name",
}
SAVE_TARGET = "save_settings"


def apply(proposal, case):
    state = deepcopy(case["state"])
    name, args = proposal.get("name"), proposal.get("arguments", {})
    if name == "YIELD":
        return state, {}
    if name == "NO_ACTION":
        intent = case["request"].get("intent")
        field = INTENT_TO_FIELD.get(intent)
        if field is None:
            return state, {}
        current = state.get("values", {}).get(field)
        requested = case["request"].get("value")
        return state, ({field: current} if current == requested else {})
    if args.get("scope_id") != state.get("scope_id") or args.get("generation") != state.get("generation"):
        raise ValueError("STALE_ACTION")
    if name == "SET_FIELD":
        field, value = args.get("field"), args.get("value")
        if value not in state.get("allowed_values", {}).get(field, []):
            raise ValueError("UNSUPPORTED_FIELD_VALUE")
        state.setdefault("staged", {})[field] = value
        return state, {}
    if name == "CLICK":
        target = args.get("target")
        if target not in state.get("visible_targets", []):
            raise ValueError("TARGET_NOT_VISIBLE")
        if target in TARGET_TO_FIELD:
            field = TARGET_TO_FIELD[target]
            current = state.get("values", {}).get(field)
            if not isinstance(current, bool):
                raise ValueError("TOGGLE_STATE_NOT_BOOLEAN")
            state["values"][field] = not current
            return state, {field: state["values"][field]}
        if target == SAVE_TARGET:
            staged = state.get("staged", {})
            if len(staged) != 1:
                raise ValueError("SAVE_REQUIRES_EXACTLY_ONE_STAGED_FIELD")
            field, value = next(iter(staged.items()))
            if value not in state.get("allowed_values", {}).get(field, []):
                raise ValueError("STAGED_VALUE_UNSUPPORTED")
            state.setdefault("values", {})[field] = value
            state["staged"] = {}
            return state, {field: value, "saved": True}
        raise ValueError("UNKNOWN_CLICK_TARGET")
    raise ValueError("UNKNOWN_ACTION")


def audit(cases, result):
    errors = []
    case_by_id = {case["id"]: case for case in cases}
    rows = result.get("rows", [])
    if len(rows) != len(cases) or len({row.get("id") for row in rows}) != len(rows):
        errors.append("ROW_CARDINALITY_OR_DUPLICATE")
    if {row.get("id") for row in rows} != set(case_by_id):
        errors.append("ROW_CASE_SET")
    row_by_id = {row.get("id"): row for row in rows}
    for case_id, case in case_by_id.items():
        row = row_by_id.get(case_id)
        if row is None:
            continue
        if row.get("expected") != case.get("expected"):
            errors.append("FIXTURE_EXPECTED_MISMATCH:" + case_id)
        if row.get("proposal") != case.get("expected"):
            errors.append("PROPOSAL_MISMATCH:" + case_id)
        if row.get("authority") != case.get("authority"):
            errors.append("AUTHORITY_MISMATCH:" + case_id)
        try:
            next_state, postcondition = apply(row.get("proposal", {}), case)
            if postcondition != case.get("effect"):
                errors.append("INDEPENDENT_POSTCONDITION_MISMATCH:" + case_id)
            if row.get("effect") != postcondition:
                errors.append("CLAIMED_POSTCONDITION_MISMATCH:" + case_id)
            if row["proposal"].get("name") in {"YIELD", "NO_ACTION"} and next_state != case["state"]:
                errors.append("NOOP_MUTATED_STATE:" + case_id)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append("TRANSITION_REJECTED:" + case_id + ":" + str(exc))
    field_row = row_by_id.get("multistep_set_field", {})
    save_row = row_by_id.get("multistep_save", {})
    linked = (
        field_row.get("proposal", {}).get("name") == "SET_FIELD"
        and field_row.get("proposal", {}).get("arguments", {}).get("field") == "digest_frequency"
        and field_row.get("proposal", {}).get("arguments", {}).get("value")
        == case_by_id.get("multistep_save", {}).get("state", {}).get("staged", {}).get("digest_frequency")
        and save_row.get("proposal", {}).get("name") == "CLICK"
        and save_row.get("proposal", {}).get("arguments", {}).get("target") == SAVE_TARGET
        and save_row.get("prior_step_ok") is True
    )
    if not linked:
        errors.append("MULTISTEP_LINK_INVALID")
    return {"schema": "issue4680-independent-postcondition-audit-v3", "decision": "PASS_POSTCONDITION_ORACLE_SCOPED" if not errors else "FAIL_POSTCONDITION_ORACLE", "rows_checked": len(rows), "errors": errors}

