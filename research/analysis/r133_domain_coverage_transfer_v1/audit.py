"""Independent raw-only audit of the frozen domain coverage reconstruction."""

import json
import pathlib
import sys

from frozen_sources import load_inputs_from_payload


def main():
    if len(sys.argv) != 3 or sys.argv[1] != "--stdin":
        raise SystemExit("usage: audit.py --stdin CANDIDATE.json")
    root = pathlib.Path(__file__).resolve().parent
    candidate_path = pathlib.Path(sys.argv[2])
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    inputs, provenance = load_inputs_from_payload(sys.stdin.buffer.read())
    expected = {
        "schema": "r133-domain-coverage-vector-v1",
        "domains": {
            "doom_physical_r1": {"held_input_occupancy": {
                "status": "MEASURED_BOUNDED",
                "scope": "XTEST_OWNER_BRACKETS",
                "paired_actuation_edges": 6,
                "max_censor_width_ms": 0.559054,
                "continuous_map01_occupancy_duration_measured": False,
            }},
            "doom_v38_v39": {"held_input_occupancy": {
                "status": "INTERVAL_CENSORED",
                "runs": {
                    "v38": {"hold_steps": 11, "lower_ms": 3048.89, "upper_ms": 4039.878,
                            "interval_width_ms": 990.987, "precision_gate_passed": True},
                    "v39": {"hold_steps": 29, "lower_ms": 6301.2, "upper_ms": 8452.733,
                            "interval_width_ms": 2151.534, "precision_gate_passed": False},
                },
            }, "useful_feedback": {
                "status": "PARTIAL_STATE_FEEDBACK_ONLY",
                "plans_with_state_feedback": 3,
                "admitted_plans": 4,
                "plan_bound_task_effects": 0,
            }},
            "calc_final_wait": {
                "held_input_occupancy": {"status": "RELEASE_ONLY", "duration_measured": False},
                "task_outcome": {"status": "SAVED_OUTPUT_VERIFIED_UNTIMED", "verified_rows": 4, "rows": 4},
                "useful_feedback": {"status": "OBSERVATION_COUNT_ONLY", "extra_observations": 2,
                                    "first_useful_time_identifiable": False},
            },
        },
    }
    if candidate != expected:
        audit = {"decision": "FAIL", "errors": ["candidate_differs_from_independent_reconstruction"],
                 "provenance": provenance}
    else:
        audit = {"decision": "PASS", "errors": [], "provenance": provenance,
                 "scope": "posthoc evidence classification only; no new GUI/model/input allocation"}
    (candidate_path.parent / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return 0 if audit["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
