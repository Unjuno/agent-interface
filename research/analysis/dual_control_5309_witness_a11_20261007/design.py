"""A11 fixture: topology-specific transitions determine immediate witness survival."""
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUDGET = 1
TOPOLOGIES = {
    "cycle3": {
        "states": ["c0", "c1", "c2"], "witness_state": "c1",
        "edges": {"c0": {"action-a": "c1", "action-b": "c2"},
                  "c1": {"action-a": "c2", "action-b": "c0"},
                  "c2": {"action-a": "c0", "action-b": "c1"}},
    },
    "branch_merge": {
        "states": ["m0", "m1", "m2", "m3"], "witness_state": "m3",
        "edges": {"m0": {"action-a": "m1", "action-b": "m2"},
                  "m1": {"action-a": "m3", "action-b": "m0"},
                  "m2": {"action-a": "m0", "action-b": "m3"},
                  "m3": {"action-a": "m1", "action-b": "m2"}},
    },
    "asymmetric4": {
        "states": ["u0", "u1", "u2", "u3"], "witness_state": "u3",
        "edges": {"u0": {"action-a": "u1", "action-b": "u2"},
                  "u1": {"action-a": "u0", "action-b": "u3"},
                  "u2": {"action-a": "u3", "action-b": "u1"},
                  "u3": {"action-a": "u2", "action-b": "u0"}},
    },
}


def build():
    cases, truth, profiles = [], {}, {}
    index = 0
    for topology, graph in TOPOLOGIES.items():
        for state, correct, cost, prior in itertools.product(
            graph["states"], (True, False), (0, 1, 2), (False, True)
        ):
            index += 1
            cid = f"a11-{index:03d}"
            actual = {action: (dest == graph["witness_state"])
                      for action, dest in graph["edges"][state].items()}
            predicted = dict(actual if correct else {a: not value for a, value in actual.items()})
            costs = {"action-a": 0, "action-b": cost}
            cases.append({"case_id": cid, "topology": topology, "state": state,
                          "admissible_actions": ["action-a", "action-b"],
                          "predicted_ig_bits": {"action-a": 1.0, "action-b": 1.0},
                          "predicted_witness_survival": predicted,
                          "preservation_cost": costs, "cost_budget": BUDGET,
                          "preexisting_witness": prior})
            truth[cid] = {"topology": topology, "state": state,
                          "next_state_by_action": graph["edges"][state],
                          "witness_state": graph["witness_state"],
                          "correct_commit_by_next_state": {s: f"commit-{s}" for s in graph["states"]}}
        profiles[topology] = {s: {a: (d == graph["witness_state"])
                                  for a, d in graph["edges"][s].items()}
                              for s in graph["states"]}
    return {"allocation": "5309-TOPOLOGY-DEPENDENT-A11-HOST-20261007", "cases": cases}, {
        "allocation": "5309-TOPOLOGY-DEPENDENT-A11-HOST-20261007",
        "topologies": TOPOLOGIES, "truth_by_case_id": truth, "profiles": profiles}


if __name__ == "__main__":
    workload, oracle = build()
    (ROOT / "candidate-input.json").write_text(json.dumps(workload, sort_keys=True, separators=(",", ":")) + "\n")
    (ROOT / "oracle.json").write_text(json.dumps(oracle, sort_keys=True, separators=(",", ":")) + "\n")
