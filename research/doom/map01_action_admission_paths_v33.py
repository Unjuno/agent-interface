"""Deterministic all-path receipt/program cardinality replay for MAP01 v33."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "live_control"))
import map01_overlap_controller_v33 as controller
from final_action_admission_v2 import record_post_admission_revocation


BINDING = {"focus": 1, "surface": 1, "geometry": [0, 0, 640, 480]}
ACTION = {"assessment": "typed construction", "state": "active",
          "commands": [{"action": "retreat_fire", "extent": "short"}],
          "contingencies": [],
          "next_cover": [{"action": "strafe_left", "extent": "short"}],
          "next_cover_validity": [{"signal_id": "health",
                                   "critical_health_minimum": 45,
                                   "maximum_health_loss": 8,
                                   "max_source_age_ms": 30000}],
          "action_validity": [{"critical_health_minimum": 45,
                               "maximum_health_loss": 8,
                               "minimum_ammo": 1,
                               "max_current_age_ms": 500}]}


def signal(signal_id, value, sequence, capture_ns, status="observed"):
    return {"format": "observable-signal-v1", "status": status,
            "signal_id": signal_id, "value": value if status == "observed" else None,
            "sequence": sequence, "capture_ns": capture_ns, "binding": BINDING}


def planner(status="completed", eligible=True):
    return SimpleNamespace(handle=SimpleNamespace(turn_id="turn-replay"),
                           status=status, answer_eligible=eligible)


def initial(status="completed", eligible=True, invalidation=None, decided=11):
    return controller.final_admission_from_planner_result(
        planner(status, eligible), 10, invalidation, decided)


def hard(observed=20):
    return {"outcome_evaluated_ns": observed, "outcome": {
        "status": "HARD_INVALIDATED", "reason": "below_hard_minimum",
        "requires_new_decision": True, "grants_input_authority": False}}


def action_result(current_health=79, ammo_status="observed"):
    return controller.prepare_action_admission(
        initial(), ACTION, ACTION["action_validity"][0],
        signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
        signal("health", current_health, 2, 200),
        signal("ammo", 46, 2, 200, status=ammo_status), 201)


def run():
    policy = initial(invalidation=hard(20), decided=21)
    ineligible = initial(status="interrupted", eligible=False)
    controller_invalid = controller.record_controller_no_input(
        initial(), "controller_validation_failed")
    terminal = controller.record_controller_no_input(
        initial(), "terminal_model_state")
    health_invalid = action_result(current_health=76)
    ammo_unknown = action_result(ammo_status="unknown")
    active = controller.bind_first_plan_acceptance(
        action_result(), {"id": "plan-primary", "accepted_ns": 202})
    revoked = record_post_admission_revocation(active, hard(203), 204)
    cases = [
        ("policy_invalidated", policy, 0, False),
        ("planner_ineligible", ineligible, 0, False),
        ("controller_invalid", controller_invalid, 0, False),
        ("terminal_no_input", terminal, 0, False),
        ("action_health_invalid", health_invalid, 0, False),
        ("action_ammo_unknown", ammo_unknown, 0, False),
        ("active_first_acceptance", active, 1, True),
        ("active_then_revoked", revoked, 1, False),
    ]
    rows = []
    for name, receipt, historical_accepts, current_authority in cases:
        observed_accepts = int(receipt["executor_admission"] is not None)
        assert observed_accepts == historical_accepts
        assert receipt["input_authority_admitted"] is current_authority
        if historical_accepts == 0:
            assert receipt["executor_admission"] is None
        rows.append({"case": name, "status": receipt["status"],
                     "historical_executor_acceptances": observed_accepts,
                     "current_input_authority": current_authority,
                     "receipt": receipt})
    assert health_invalid["reason"] == "REJECTED_PREDICATE"
    assert ammo_unknown["reason"] == "REJECTED_SIGNAL_UNKNOWN"
    return {"schema": "map01-action-admission-path-replay-v33",
            "passed": True, "cases": rows, "total_cases": len(rows),
            "zero_primary_admission_cases": 6,
            "first_acceptance_cases": 1, "post_acceptance_revocation_cases": 1,
            "model_calls": 0, "input_operations": 0,
            "invariant": "planner/policy/controller/current-action no-input paths have zero Executor acceptance; only recomputed VALID_CURRENT can bind the first acceptance; revocation retains historical acceptance with no current authority",
            "limits": "deterministic state-machine/controller composition only; no endpoint, live game, timing, planner authorship, usefulness or gameplay claim"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "audit.json").write_bytes(
        (json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"passed": result["passed"],
                      "total_cases": result["total_cases"],
                      "zero_primary_admission_cases": result["zero_primary_admission_cases"]},
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
