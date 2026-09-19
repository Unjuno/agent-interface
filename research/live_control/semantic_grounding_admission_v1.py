"""Convert typed model invocation outcomes into a no-authority task boundary."""


OUTCOME_SCHEMA = "semantic-grounding-invocation-outcome-v1"
RECEIPT_SCHEMA = "semantic-grounding-admission-v1"
STATUSES = {"COMPLETED", "DEFERRED_UPSTREAM", "FAILED_UPSTREAM", "FAILED_OUTPUT"}


def admit(outcome):
    if type(outcome) is not dict or outcome.get("schema") != OUTCOME_SCHEMA:
        raise ValueError("typed semantic invocation outcome required")
    status = outcome.get("status")
    if status not in STATUSES:
        raise ValueError("known invocation status required")
    if outcome.get("grants_semantic_authority") is not False or \
            outcome.get("grants_input_authority") is not False:
        raise ValueError("invocation outcome must grant no authority")
    base = {"schema": RECEIPT_SCHEMA, "invocation_status": status,
            "requested_model": outcome.get("requested_model"),
            "requested_effort": outcome.get("requested_effort"),
            "grants_semantic_authority": False, "grants_input_authority": False,
            "ordinary_executor_admission_required": True}
    if status == "COMPLETED":
        result, usage = outcome.get("result"), outcome.get("usage")
        if type(result) is not dict or type(result.get("grounding")) is not dict or \
                type(result.get("call_id")) is not str or not result["call_id"] or \
                type(usage) is not dict or type(usage.get("input_tokens")) is not int:
            raise ValueError("validated completed grounding required")
        return {**base, "status": "TASK_MUTATION_ELIGIBLE",
                "reason": "current_grounding_completed", "task_mutation_eligible": True,
                "grounding_reference": result["grounding"],
                "model_call_id": result["call_id"], "usage": usage}
    expected_reason = {"DEFERRED_UPSTREAM": "capacity_unavailable",
                       "FAILED_UPSTREAM": "model_process_failed",
                       "FAILED_OUTPUT": "invalid_model_output"}[status]
    if outcome.get("reason") != expected_reason or outcome.get("result") is not None or \
            outcome.get("usage") is not None:
        raise ValueError("exact noncompleted invocation outcome required")
    return {**base,
            "status": "TASK_DEFERRED" if status == "DEFERRED_UPSTREAM" else "TASK_BLOCKED",
            "reason": expected_reason, "task_mutation_eligible": False,
            "grounding_reference": None, "model_call_id": None, "usage": None}
