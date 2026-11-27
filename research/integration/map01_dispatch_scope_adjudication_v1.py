"""Classify public Win32 dispatch rows that stop before task input."""


def adjudicate_dispatch_scope(row):
    """Return a fail-closed scope classification without inferring release.

    The public dispatch envelope can report that no operation was invoked
    while the nested source action remains UNKNOWN and automatic recovery is
    also UNKNOWN. This is a pre-task stop, not a successful recovery or a
    completed task effect.
    """
    if type(row) is not dict:
        return {"classification": "UNCLASSIFIED", "errors": ["row_not_object"]}

    action = row.get("action")
    cancellation = row.get("cancellation")
    recovery = cancellation.get("result") if type(cancellation) is dict else None
    if type(action) is not dict or type(cancellation) is not dict \
            or type(recovery) is not dict:
        return {"classification": "UNCLASSIFIED",
                "errors": ["required_scopes_missing"]}

    errors = []
    if row.get("input_dispatched") is not False:
        errors.append("outer_dispatch_not_false")
    if row.get("operation_invoked") is not False:
        errors.append("operation_invoked_not_false")
    if row.get("task_success") is not None:
        errors.append("outer_task_success_not_null")
    if row.get("replay_allowed") is not False:
        errors.append("outer_replay_not_denied")

    if action.get("status") != "unknown":
        errors.append("source_action_not_unknown")
    if action.get("input_dispatched") is not None:
        errors.append("source_dispatch_claim_not_unknown")
    if action.get("release_confirmed") is not False:
        errors.append("source_release_not_unconfirmed")
    if action.get("task_success") is not None:
        errors.append("source_task_success_not_null")
    if action.get("replay_allowed") is not False:
        errors.append("source_replay_not_denied")
    operation_id = action.get("operation_id")
    generation = action.get("target_generation")
    if type(operation_id) is not str or len(operation_id) != 32:
        errors.append("source_operation_id_invalid")
    if type(generation) is not str or len(generation) != 64:
        errors.append("source_generation_invalid")

    if cancellation.get("automatic_completion_recovery") is not True:
        errors.append("automatic_recovery_not_identified")
    if cancellation.get("status") != "unknown" \
            or cancellation.get("release_confirmed") is not False:
        errors.append("cancellation_not_unknown_unreleased")
    if cancellation.get("replay_allowed") is not False:
        errors.append("cancellation_replay_not_denied")
    if cancellation.get("action_operation_id") != operation_id:
        errors.append("cancellation_source_operation_mismatch")
    if cancellation.get("target_generation") != generation:
        errors.append("cancellation_source_generation_mismatch")

    if recovery.get("status") != "unknown" \
            or recovery.get("release_confirmed") is not False:
        errors.append("recovery_result_not_unknown_unreleased")
    if recovery.get("completion_readback_outcome") != "not_attempted":
        errors.append("completion_readback_scope_mismatch")
    if recovery.get("late_input_horizon_ns") != 0:
        errors.append("late_input_horizon_claim_mismatch")
    if recovery.get("operation_id") != operation_id:
        errors.append("recovery_source_operation_mismatch")
    if recovery.get("target_generation") != generation:
        errors.append("recovery_source_generation_mismatch")
    if recovery.get("task_success") is not None \
            or recovery.get("replay_allowed") is not False:
        errors.append("recovery_task_or_replay_scope_mismatch")

    attempts = recovery.get("recovery_release_attempts")
    returned_up_domains = set()
    if type(attempts) is list and len(attempts) <= 128:
        for attempt in attempts:
            if (type(attempt) is dict
                    and attempt.get("outcome") == "returned"
                    and attempt.get("sendinput_call_started") is True
                    and type(attempt.get("sendinput_return_count")) is int
                    and attempt.get("sendinput_return_count") == 1
                    and attempt.get("sendinput_error_type") is None):
                returned_up_domains.add(attempt.get("domain"))

    if errors:
        return {"classification": "UNCLASSIFIED", "errors": errors,
                "release_attempts_returned": sorted(returned_up_domains),
                "task_success": None, "replay_allowed": False}

    return {
        "classification": "NO_TASK_DISPATCH_RECOVERY_UNVERIFIED",
        "errors": [],
        "source_operation_id": action.get("operation_id"),
        "target_generation": action.get("target_generation"),
        "recovery_release_attempts_returned": sorted(returned_up_domains),
        "release_confirmed": False,
        "late_input_horizon_ns": 0,
        "task_success": None,
        "replay_allowed": False,
    }
