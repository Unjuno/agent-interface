"""Typed controller admission receipts across planner/policy race orderings."""
from copy import deepcopy


SCHEMA = "final-action-admission-v1"


def _turn(value):
    expected = {"turn_id", "status", "answer_eligible", "terminal_observed_ns"}
    if (type(value) is not dict or set(value) != expected or
            not isinstance(value["turn_id"], str) or not value["turn_id"] or
            value["status"] not in ("completed", "interrupted", "failed") or
            type(value["answer_eligible"]) is not bool or
            type(value["terminal_observed_ns"]) is not int or
            value["terminal_observed_ns"] < 0):
        raise ValueError("exact planner terminal receipt required")
    return value


def _invalidation(value):
    if value is None:
        return None
    outcome = value.get("outcome") if type(value) is dict else None
    if (type(outcome) is not dict or
            outcome.get("status") in (None, "VALID", "SOFT_CHANGED") or
            outcome.get("requires_new_decision") is not True or
            outcome.get("grants_input_authority") is not False or
            type(value.get("outcome_evaluated_ns")) is not int or
            value["outcome_evaluated_ns"] < 0):
        raise ValueError("exact authority-reducing invalidation required")
    return value


def decide_final_admission(planner_terminal, policy_invalidation, controller_decided_ns):
    """Resolve both observed boundaries; this function never issues input."""
    turn = _turn(planner_terminal)
    invalidation = _invalidation(policy_invalidation)
    if type(controller_decided_ns) is not int or controller_decided_ns < 0:
        raise ValueError("controller_decided_ns must be monotonic integer time")
    observed = [turn["terminal_observed_ns"]]
    if invalidation is not None:
        observed.append(invalidation["outcome_evaluated_ns"])
    if max(observed) > controller_decided_ns:
        raise ValueError("controller decision precedes observed boundary")
    if invalidation is not None:
        status = "REJECTED_POLICY_INVALIDATED"
        reason = invalidation["outcome"].get("reason", "policy_invalidated")
    elif turn["status"] != "completed" or turn["answer_eligible"] is not True:
        status = "REJECTED_PLANNER_INELIGIBLE"
        reason = f"planner_{turn['status']}"
    else:
        status = "READY_FOR_FRESH_EXECUTOR_ADMISSION"
        reason = "planner_complete_and_policy_current"
    return {
        "schema": SCHEMA,
        "status": status,
        "reason": reason,
        "planner_terminal": deepcopy(turn),
        "policy_invalidation": deepcopy(invalidation),
        "controller_decided_ns": controller_decided_ns,
        "input_authority_admitted": False,
        "executor_admission": None,
        "revocation": None,
        "grants_input_authority": False,
    }


def record_executor_admission(receipt, accepted):
    """Bind a READY receipt to an already-observed executor acceptance."""
    if (type(receipt) is not dict or receipt.get("schema") != SCHEMA or
            receipt.get("status") != "READY_FOR_FRESH_EXECUTOR_ADMISSION" or
            receipt.get("input_authority_admitted") is not False or
            receipt.get("executor_admission") is not None):
        raise ValueError("only a fresh READY receipt can bind executor admission")
    expected = {"event", "id", "accepted_ns"}
    if (type(accepted) is not dict or set(accepted) != expected or
            accepted["event"] != "accepted" or
            not isinstance(accepted["id"], str) or not accepted["id"] or
            type(accepted["accepted_ns"]) is not int or
            accepted["accepted_ns"] < receipt["controller_decided_ns"]):
        raise ValueError("exact later executor acceptance required")
    result = deepcopy(receipt)
    result.update({
        "status": "INPUT_ADMITTED",
        "reason": "fresh_executor_acceptance_observed",
        "input_authority_admitted": True,
        "executor_admission": deepcopy(accepted),
        "grants_input_authority": False,
    })
    return result


def record_controller_no_input(receipt, reason):
    """Close a READY receipt when controller semantics require no motor input."""
    if (type(receipt) is not dict or receipt.get("schema") != SCHEMA or
            receipt.get("status") != "READY_FOR_FRESH_EXECUTOR_ADMISSION" or
            receipt.get("input_authority_admitted") is not False or
            receipt.get("executor_admission") is not None or
            reason not in ("terminal_model_state", "controller_validation_failed")):
        raise ValueError("exact READY no-input transition required")
    result = deepcopy(receipt)
    result.update({
        "status": ("NO_INPUT_TERMINAL_STATE" if reason == "terminal_model_state"
                   else "REJECTED_CONTROLLER_VALIDATION"),
        "reason": reason,
        "grants_input_authority": False,
    })
    return result


def record_post_admission_revocation(receipt, policy_invalidation, controller_decided_ns):
    """Record a later revocation without rewriting the historical admission."""
    invalidation = _invalidation(policy_invalidation)
    if (type(receipt) is not dict or receipt.get("schema") != SCHEMA or
            receipt.get("status") != "INPUT_ADMITTED" or
            receipt.get("input_authority_admitted") is not True):
        raise ValueError("only an admitted receipt can be revoked")
    accepted_ns = receipt["executor_admission"]["accepted_ns"]
    if (invalidation["outcome_evaluated_ns"] < accepted_ns or
            type(controller_decided_ns) is not int or
            controller_decided_ns < invalidation["outcome_evaluated_ns"]):
        raise ValueError("revocation must follow admission and observed invalidation")
    result = deepcopy(receipt)
    result.update({
        "status": "REVOKED_POLICY_INVALIDATED",
        "reason": invalidation["outcome"].get("reason", "policy_invalidated"),
        "input_authority_admitted": False,
        "revocation": {
            "policy_invalidation": deepcopy(invalidation),
            "controller_decided_ns": controller_decided_ns,
        },
        "grants_input_authority": False,
    })
    return result
