"""Final admission with a mandatory fresh action-validity stage."""
from copy import deepcopy

from final_action_admission_v1 import (
    decide_final_admission as decide_v1,
    record_controller_no_input as no_input_v1)
from action_validity_admission_v1 import evaluate_action_validity


SCHEMA = "final-action-admission-v2"
ACTION_VALIDITY_FORMAT = "action-validity-admission-v1"


def _v2(value):
    if type(value) is not dict or value.get("schema") != SCHEMA:
        raise ValueError("final-action-admission-v2 receipt required")
    return value


def decide_final_admission(planner_terminal, policy_invalidation, controller_decided_ns):
    """Resolve planner/policy boundaries before inspecting a returned action."""
    receipt = decide_v1(planner_terminal, policy_invalidation, controller_decided_ns)
    receipt["schema"] = SCHEMA
    receipt["action_validity"] = None
    if receipt["status"] == "READY_FOR_FRESH_EXECUTOR_ADMISSION":
        receipt["status"] = "READY_FOR_ACTION_VALIDITY"
        receipt["reason"] = "planner_complete_and_policy_current_requires_fresh_action_check"
    return receipt


def record_controller_no_input(receipt, reason):
    """Close a clean planner result before motor admission."""
    receipt = _v2(receipt)
    if (receipt.get("status") != "READY_FOR_ACTION_VALIDITY" or
            receipt.get("action_validity") is not None):
        raise ValueError("only a fresh action-validity-ready receipt can close no-input")
    adapted = deepcopy(receipt)
    adapted["schema"] = "final-action-admission-v1"
    adapted["status"] = "READY_FOR_FRESH_EXECUTOR_ADMISSION"
    adapted.pop("action_validity")
    closed = no_input_v1(adapted, reason)
    closed["schema"] = SCHEMA
    closed["action_validity"] = None
    return closed


def record_action_validity(receipt, action, validity):
    """Bind an already-evaluated current-state result; no input is issued here."""
    receipt = _v2(receipt)
    if (receipt.get("status") != "READY_FOR_ACTION_VALIDITY" or
            receipt.get("action_validity") is not None or
            receipt.get("executor_admission") is not None or
            receipt.get("input_authority_admitted") is not False):
        raise ValueError("fresh READY_FOR_ACTION_VALIDITY receipt required")
    if (type(validity) is not dict or validity.get("format") != ACTION_VALIDITY_FORMAT or
            type(validity.get("action_may_proceed_to_executor_admission")) is not bool or
            validity.get("grants_input_authority") is not False or
            type(validity.get("controller_decided_ns")) is not int or
            validity["controller_decided_ns"] < receipt["controller_decided_ns"]):
        raise ValueError("exact later no-authority action-validity result required")
    try:
        recomputed = evaluate_action_validity(
            action, validity["contract"], validity["snapshot"],
            validity["controller_decided_ns"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("complete reproducible action-validity result required") from error
    if recomputed != validity:
        raise ValueError("action-validity result does not match deterministic reevaluation")
    result = deepcopy(receipt)
    result["action_validity"] = deepcopy(validity)
    if (validity["status"] == "VALID_CURRENT" and
            validity["action_may_proceed_to_executor_admission"] is True and
            validity.get("requires_new_decision") is False):
        result["status"] = "READY_FOR_FRESH_EXECUTOR_ADMISSION"
        result["reason"] = "planner_policy_and_action_current"
    elif (validity["status"].startswith("REJECTED_") and
          validity["action_may_proceed_to_executor_admission"] is False and
          validity.get("requires_new_decision") is True):
        result["status"] = "REJECTED_ACTION_NOT_CURRENT"
        result["reason"] = validity["status"]
    else:
        raise ValueError("inconsistent action-validity result")
    return result


def record_executor_admission(receipt, accepted):
    """Bind the first actual Executor acceptance after current-state validation."""
    receipt = _v2(receipt)
    validity = receipt.get("action_validity")
    expected = {"event", "id", "accepted_ns"}
    if (receipt.get("status") != "READY_FOR_FRESH_EXECUTOR_ADMISSION" or
            type(validity) is not dict or validity.get("status") != "VALID_CURRENT" or
            receipt.get("input_authority_admitted") is not False or
            receipt.get("executor_admission") is not None or
            type(accepted) is not dict or set(accepted) != expected or
            accepted["event"] != "accepted" or
            not isinstance(accepted["id"], str) or not accepted["id"] or
            type(accepted["accepted_ns"]) is not int or
            accepted["accepted_ns"] < validity["controller_decided_ns"]):
        raise ValueError("fresh Executor acceptance after VALID_CURRENT required")
    result = deepcopy(receipt)
    result.update({"status": "INPUT_ADMITTED",
                   "reason": "fresh_executor_acceptance_after_action_validation",
                   "input_authority_admitted": True,
                   "executor_admission": deepcopy(accepted),
                   "grants_input_authority": False})
    return result


def record_post_admission_revocation(receipt, policy_invalidation, controller_decided_ns):
    """Record later revocation while retaining the historical acceptance."""
    receipt = _v2(receipt)
    if (receipt.get("status") != "INPUT_ADMITTED" or
            receipt.get("input_authority_admitted") is not True or
            type(policy_invalidation) is not dict):
        raise ValueError("admitted v2 receipt and invalidation required")
    outcome = policy_invalidation.get("outcome")
    accepted_ns = receipt["executor_admission"]["accepted_ns"]
    if (type(outcome) is not dict or outcome.get("requires_new_decision") is not True or
            outcome.get("grants_input_authority") is not False or
            outcome.get("status") in (None, "VALID", "SOFT_CHANGED") or
            type(policy_invalidation.get("outcome_evaluated_ns")) is not int or
            policy_invalidation["outcome_evaluated_ns"] < accepted_ns or
            type(controller_decided_ns) is not int or
            controller_decided_ns < policy_invalidation["outcome_evaluated_ns"]):
        raise ValueError("exact later authority-reducing invalidation required")
    result = deepcopy(receipt)
    result.update({"status": "REVOKED_POLICY_INVALIDATED",
                   "reason": outcome.get("reason", "policy_invalidated"),
                   "input_authority_admitted": False,
                   "revocation": {"policy_invalidation": deepcopy(policy_invalidation),
                                  "controller_decided_ns": controller_decided_ns},
                   "grants_input_authority": False})
    return result
