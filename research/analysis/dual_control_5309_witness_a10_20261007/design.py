"""Frozen A10 finite fixture generator; truth stays in oracle.json by convention only."""
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUDGET = 1
TOPOLOGIES = {
    "cycle3": {
        "states": ["c0", "c1", "c2"],
        "edges": {"c0": {"action-a": "c1", "action-b": "c2"},
                  "c1": {"action-a": "c2", "action-b": "c0"},
                  "c2": {"action-a": "c0", "action-b": "c1"}},
        "preserves": {"action-a": False, "action-b": True},
    },
    "branch_merge": {
        "states": ["m0", "m1", "m2", "m3"],
        "edges": {"m0": {"action-a": "m1", "action-b": "m2"},
                  "m1": {"action-a": "m3", "action-b": "m3"},
                  "m2": {"action-a": "m3", "action-b": "m3"},
                  "m3": {"action-a": "m0", "action-b": "m0"}},
        "preserves": {"action-a": False, "action-b": True},
    },
    "asymmetric4": {
        "states": ["u0", "u1", "u2", "u3"],
        "edges": {"u0": {"action-a": "u1", "action-b": "u2"},
                  "u1": {"action-a": "u0", "action-b": "u3"},
                  "u2": {"action-a": "u3", "action-b": "u1"},
                  "u3": {"action-a": "u2", "action-b": "u0"}},
        "preserves": {"action-a": False, "action-b": True},
    },
}


def build():
    candidate, truth = [], {}
    idx = 0
    for topology, spec in TOPOLOGIES.items():
        for state, model_correct, cost, prior_witness in itertools.product(
            spec["states"], (True, False), (0, 1, 2), (False, True)
        ):
            idx += 1
            case_id = f"a10-{idx:03d}"
            actual = dict(spec["preserves"])
            predicted = dict(actual if model_correct else {"action-a": True, "action-b": False})
            action_cost = {"action-a": 0, "action-b": cost}
            candidate.append({
                "case_id": case_id, "topology": topology, "state": state,
                "admissible_actions": ["action-a", "action-b"],
                "predicted_ig_bits": {"action-a": 1.0, "action-b": 1.0},
                "predicted_witness_survival": predicted,
                "preservation_cost": action_cost, "cost_budget": BUDGET,
                "preexisting_witness": prior_witness,
            })
            truth[case_id] = {
                "topology": topology, "state": state,
                "next_state_by_action": spec["edges"][state],
                "witness_survival_by_action": actual,
                "correct_commit_by_next_state": {node: f"commit-{node}" for node in spec["states"]},
            }
    return {"allocation": "5309-WITNESS-A10-HOST-20261007", "cases": candidate}, {
        "allocation": "5309-WITNESS-A10-HOST-20261007", "topologies": TOPOLOGIES,
        "truth_by_case_id": truth,
    }


if __name__ == "__main__":
    workload, oracle = build()
    (ROOT / "candidate-input.json").write_text(json.dumps(workload, sort_keys=True, separators=(",", ":")) + "\n")
    (ROOT / "oracle.json").write_text(json.dumps(oracle, sort_keys=True, separators=(",", ":")) + "\n")
