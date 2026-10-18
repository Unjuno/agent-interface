"""Deterministic finite trace fixture for Issue #8397 T0 A02."""
import argparse
import json
from pathlib import Path


def build_records():
    return {
        "allocation": "OBS-OMISSION-REGRET-8397-T0-A02-20261008",
        "episodes": [
            {
                "id": "pre_decision",
                "state": "before_observation_sensitive_decision",
                "arm": "baseline",
                "interval": [0, 0],
                "captured": 3,
                "delivered": 3,
                "visible_bytes": 300,
                "mandatory_cue_delivered": True,
                "decision": "act_on_current_A",
                "task_effect": "A_applied",
                "recovery_steps": 0,
                "stop_outcome": "completed_exactly",
            },
            {
                "id": "pre_decision",
                "state": "before_observation_sensitive_decision",
                "arm": "omission",
                "interval": [0, 1],
                "captured": 2,
                "delivered": 2,
                "visible_bytes": 200,
                "mandatory_cue_delivered": True,
                "decision": "act_on_current_A_after_resume",
                "task_effect": "A_applied",
                "recovery_steps": 0,
                "stop_outcome": "completed_exactly",
            },
            {
                "id": "cross_transition",
                "state": "crosses_target_change_before_decision",
                "arm": "baseline",
                "interval": [0, 0],
                "captured": 3,
                "delivered": 3,
                "visible_bytes": 300,
                "mandatory_cue_delivered": True,
                "decision": "act_on_current_B",
                "task_effect": "B_applied",
                "recovery_steps": 0,
                "stop_outcome": "completed_exactly",
            },
            {
                "id": "cross_transition",
                "state": "crosses_target_change_before_decision",
                "arm": "omission",
                "interval": [1, 2],
                "captured": 2,
                "delivered": 2,
                "visible_bytes": 200,
                "mandatory_cue_delivered": True,
                "decision": "act_on_stale_A_then_recover_to_B",
                "task_effect": "wrong_A_then_B_recovered",
                "recovery_steps": 1,
                "stop_outcome": "completed_after_recovery",
            },
            {
                "id": "post_completion",
                "state": "after_independently_verified_terminal_effect",
                "arm": "baseline",
                "interval": [0, 0],
                "captured": 3,
                "delivered": 3,
                "visible_bytes": 300,
                "mandatory_cue_delivered": True,
                "decision": "terminal_already_verified",
                "task_effect": "A_applied",
                "recovery_steps": 0,
                "stop_outcome": "completed_exactly",
            },
            {
                "id": "post_completion",
                "state": "after_independently_verified_terminal_effect",
                "arm": "omission",
                "interval": [2, 3],
                "captured": 2,
                "delivered": 2,
                "visible_bytes": 200,
                "mandatory_cue_delivered": True,
                "decision": "terminal_already_verified",
                "task_effect": "A_applied",
                "recovery_steps": 0,
                "stop_outcome": "completed_exactly",
            },
            {
                "id": "captured_undelivered",
                "state": "target_changes_after_capture_before_decision",
                "arm": "transport_control",
                "interval": [1, 2],
                "captured": 1,
                "delivered": 0,
                "visible_bytes": 0,
                "mandatory_cue_delivered": True,
                "decision": "act_on_stale_A",
                "task_effect": "wrong_A_applied",
                "recovery_steps": 1,
                "stop_outcome": "completed_after_recovery",
            },
            {
                "id": "mandatory_safety",
                "state": "mandatory_safety_cue_pending",
                "arm": "omission_request_rejected",
                "interval": [0, 1],
                "captured": 1,
                "delivered": 1,
                "visible_bytes": 80,
                "mandatory_cue_delivered": True,
                "decision": "no_action_until_safety_cue",
                "task_effect": "no_external_effect",
                "recovery_steps": 0,
                "stop_outcome": "omission_rejected_mandatory_cue",
            },
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    with output.open("x", encoding="utf-8") as f:
        json.dump(build_records(), f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    print("candidate emitted 8 deterministic trace records")


if __name__ == "__main__":
    main()
