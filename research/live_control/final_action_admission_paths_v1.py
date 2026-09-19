"""Deterministic all-branch replay for final action-admission cardinality."""
import argparse
import json
from pathlib import Path

from final_action_admission_v1 import (
    decide_final_admission, record_controller_no_input,
    record_executor_admission, record_post_admission_revocation)


def turn(status="completed", eligible=True, observed=10):
    return {"turn_id": "turn-replay", "status": status,
            "answer_eligible": eligible, "terminal_observed_ns": observed}


def hard(observed):
    return {"outcome_evaluated_ns": observed, "outcome": {
        "status": "HARD_INVALIDATED", "reason": "below_hard_minimum",
        "requires_new_decision": True, "grants_input_authority": False}}


def run():
    policy = decide_final_admission(turn(observed=10), hard(20), 21)
    ineligible = decide_final_admission(
        turn(status="interrupted", eligible=False, observed=10), None, 11)
    ready_validation = decide_final_admission(turn(), None, 11)
    validation = record_controller_no_input(
        ready_validation, "controller_validation_failed")
    ready_terminal = decide_final_admission(turn(), None, 11)
    terminal = record_controller_no_input(ready_terminal, "terminal_model_state")
    ready_active = decide_final_admission(turn(), None, 11)
    active = record_executor_admission(
        ready_active, {"event": "accepted", "id": "plan-primary", "accepted_ns": 12})
    revoked = record_post_admission_revocation(active, hard(13), 14)
    cases = [
        ("policy_before_admission", policy, 0, 0),
        ("planner_ineligible", ineligible, 0, 0),
        ("controller_validation", validation, 0, 0),
        ("terminal_no_input", terminal, 0, 0),
        ("active_first_acceptance", active, 1, 1),
        ("active_then_revoked", revoked, 1, 0),
    ]
    rows = []
    for name, receipt, historical_accepts, current_authority in cases:
        observed_accepts = int(receipt["executor_admission"] is not None)
        assert observed_accepts == historical_accepts
        assert int(receipt["input_authority_admitted"]) == current_authority
        if receipt["status"] != "INPUT_ADMITTED":
            assert not receipt["input_authority_admitted"]
        rows.append({
            "case": name,
            "status": receipt["status"],
            "historical_executor_acceptances": observed_accepts,
            "current_input_authority": receipt["input_authority_admitted"],
            "receipt": receipt,
        })
    return {
        "schema": "final-action-admission-path-replay-v1",
        "passed": True,
        "cases": rows,
        "invariant": "zero-plan paths have zero executor acceptance; INPUT_ADMITTED has exactly one first acceptance; revocation preserves that historical acceptance while current authority is false",
        "total_cases": len(rows),
        "zero_plan_cases": 4,
        "input_admitted_cases": 1,
        "post_admission_revoked_cases": 1,
        "model_calls": 0,
        "input_operations": 0,
        "scope": "deterministic state-machine and v32 binding construction; no live controller or performance claim",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
