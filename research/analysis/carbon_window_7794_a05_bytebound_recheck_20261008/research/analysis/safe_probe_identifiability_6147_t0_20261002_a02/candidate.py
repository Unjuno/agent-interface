#!/usr/bin/env python3
"""Finite safe-probe policy enumeration for Issue #6147 T0 (standard library only)."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

ALLOCATION = "AI-6147-T0-20261002-02"
MAX_DEPTH = 2
SAFE = ("p", "q", "recapture")
COST = {"p": 1, "q": 1, "recapture": 1}


def make_case(name):
    if name == "separable_action_different":
        outputs = {
            "A0": "READY", "B0": "READY", "A1": "READY", "B1": "READY",
            "AQ": "READY", "BQ": "READY", "AQ1": "READY", "BQ1": "READY",
            "AL": "LEFT", "BR": "RIGHT",
        }
        effects = {s: ("SUBMIT_ALLOWED" if s.startswith("A") else "SUBMIT_FORBIDDEN") for s in outputs}
        transitions = {
            "A0": {"p": "A1", "q": "AQ", "recapture": "A0"},
            "B0": {"p": "B1", "q": "BQ", "recapture": "B0"},
            "A1": {"p": "A1", "q": "AL", "recapture": "A1"},
            "B1": {"p": "B1", "q": "BR", "recapture": "B1"},
            "AQ": {"p": "AQ1", "q": "AQ1", "recapture": "AQ"},
            "BQ": {"p": "BQ1", "q": "BQ1", "recapture": "BQ"},
            "AQ1": {"p": "AQ1", "q": "AQ1", "recapture": "AQ1"},
            "BQ1": {"p": "BQ1", "q": "BQ1", "recapture": "BQ1"},
            "AL": {"p": "AL", "q": "AL", "recapture": "AL"},
            "BR": {"p": "BR", "q": "BR", "recapture": "BR"},
        }
        return {"name": name, "initial": ["A0", "B0"], "outputs": outputs,
                "effect_envelopes": effects, "transitions": transitions,
                "unsafe_probe": "u", "unsafe_successors": {"A0": "AL", "B0": "BR"}}
    if name == "action_equivalent_alias":
        outputs = {"C0": "READY", "D0": "READY", "C1": "READY", "D1": "READY"}
        transitions = {
            "C0": {"p": "C1", "q": "C1", "recapture": "C0"},
            "D0": {"p": "D1", "q": "D1", "recapture": "D0"},
            "C1": {"p": "C1", "q": "C1", "recapture": "C1"},
            "D1": {"p": "D1", "q": "D1", "recapture": "D1"},
        }
        return {"name": name, "initial": ["C0", "D0"], "outputs": outputs,
                "effect_envelopes": {s: "SAME_SAFE_EFFECT" for s in outputs},
                "transitions": transitions}
    if name == "safe_bisimulation_impossible":
        outputs = {"E0": "READY", "F0": "READY", "E1": "READY", "F1": "READY",
                   "EL": "LEFT", "FR": "RIGHT"}
        transitions = {
            "E0": {"p": "E1", "q": "E1", "recapture": "E0"},
            "F0": {"p": "F1", "q": "F1", "recapture": "F0"},
            "E1": {"p": "E1", "q": "E1", "recapture": "E1"},
            "F1": {"p": "F1", "q": "F1", "recapture": "F1"},
            "EL": {"p": "EL", "q": "EL", "recapture": "EL"},
            "FR": {"p": "FR", "q": "FR", "recapture": "FR"},
        }
        return {"name": name, "initial": ["E0", "F0"], "outputs": outputs,
                "effect_envelopes": {s: ("EFFECT_E" if s.startswith("E") else "EFFECT_F") for s in outputs},
                "transitions": transitions, "unsafe_probe": "u",
                "unsafe_successors": {"E0": "EL", "F0": "FR"},
                "bisimulation_relation": [["E0", "F0"], ["E1", "F1"]]}
    raise ValueError(name)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def is_terminal(belief, case):
    envelopes = {case["effect_envelopes"][s] for s in belief}
    if len(belief) == 1:
        return "IDENTIFIED"
    if len(envelopes) == 1:
        return "ACTION_EQUIVALENT"
    return None


def enumerate_trees(belief, depth, case):
    terminal = is_terminal(belief, case)
    if terminal is not None:
        return [{"kind": "leaf", "belief": sorted(belief), "disposition": terminal}]
    trees = [{"kind": "leaf", "belief": sorted(belief), "disposition": "YIELD"}]
    if depth == 0:
        return trees
    for probe in SAFE:
        groups = {}
        for state in belief:
            nxt = case["transitions"][state][probe]
            observed = case["outputs"][nxt]
            groups.setdefault(observed, []).append(nxt)
        branches = {o: enumerate_trees(tuple(sorted(set(states))), depth - 1, case)
                    for o, states in sorted(groups.items())}
        for choices in itertools.product(*(branches[o] for o in sorted(branches))):
            tree = {"kind": "probe", "probe": probe, "belief": sorted(belief),
                    "branches": {o: child for o, child in zip(sorted(branches), choices)}}
            trees.append(tree)
    return trees


def leaf_dispositions(tree):
    if tree["kind"] == "leaf":
        return [tree["disposition"]]
    return [d for child in tree["branches"].values() for d in leaf_dispositions(child)]


def metrics(tree, prefix_cost=0, prefix_depth=0):
    if tree["kind"] == "leaf":
        return [(prefix_depth, prefix_cost)]
    out = []
    for child in tree["branches"].values():
        out.extend(metrics(child, prefix_cost + COST[tree["probe"]], prefix_depth + 1))
    return out


def choose(tree_list):
    valid = [t for t in tree_list if all(d in ("IDENTIFIED", "ACTION_EQUIVALENT") for d in leaf_dispositions(t))]
    if not valid:
        return None
    def key(t):
        ms = metrics(t)
        return (max(x[0] for x in ms), max(x[1] for x in ms), sum(x[0] for x in ms), canonical(t))
    return min(valid, key=key)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    args = ap.parse_args()
    case_names = ("separable_action_different", "action_equivalent_alias", "safe_bisimulation_impossible")
    cases = [make_case(n) for n in case_names]
    fixture = {"safe_probes": list(SAFE), "cost": COST, "max_depth": MAX_DEPTH, "cases": cases}
    fixture_sha = hashlib.sha256(canonical(fixture).encode()).hexdigest()
    results = []
    for case in cases:
        layers = []
        for depth in range(0, MAX_DEPTH + 1):
            trees = enumerate_trees(tuple(case["initial"]), depth, case)
            selected = choose(trees)
            layers.append({
                "depth_limit": depth,
                "policy_tree_count": len(trees),
                "resolved_policy_trees": sum(all(d in ("IDENTIFIED", "ACTION_EQUIVALENT") for d in leaf_dispositions(t)) for t in trees),
                "policy_tree_sha256_sorted": hashlib.sha256("\n".join(sorted(canonical(t) for t in trees)).encode()).hexdigest(),
                "policy_trees": trees,
                "selected_policy": selected,
                "selected_worst_depth_and_cost": None if selected is None else [max(x[0] for x in metrics(selected)), max(x[1] for x in metrics(selected))],
            })
        results.append({"case": case["name"], "layers": layers})
    raw = {"allocation_id": ALLOCATION, "fixture": fixture, "fixture_sha256": fixture_sha,
           "result": results, "formal_claim": "METHOD_ONLY_FINITE_FIXTURE"}
    data = (canonical(raw) + "\n").encode()
    Path(args.raw).write_bytes(data)
    print(json.dumps({"allocation_id": ALLOCATION, "raw_path": args.raw,
                      "raw_sha256": hashlib.sha256(data).hexdigest(),
                      "bytes": len(data), "case_count": len(cases),
                      "policy_tree_counts_by_case_depth": [[x["enumerated_policy_trees"] for x in r["layers"]] for r in results]}, sort_keys=True))


if __name__ == "__main__":
    main()

