#!/usr/bin/env python3
"""One-shot finite adaptive safe-probe tree enumerator; standard library only."""
import hashlib
import itertools
import json
from pathlib import Path

ALLOCATION = "AI-6147-T0-20261003-03"
SAFE = ("p", "q", "recapture")
COST = {"p": 1, "q": 1, "recapture": 1}
DEPTH = 2
OUT = Path(__file__).with_name("RAW.json")


def fixture_cases():
    cases = []
    states = ("A0", "B0", "A1", "B1", "AQ", "BQ", "AL", "BR")
    outputs = {s: "READY" for s in states}
    outputs.update(AL="LEFT", BR="RIGHT")
    delta = {
        "A0": {"p": "A1", "q": "AQ", "recapture": "A0"},
        "B0": {"p": "B1", "q": "BQ", "recapture": "B0"},
        "A1": {"p": "A1", "q": "AL", "recapture": "A1"},
        "B1": {"p": "B1", "q": "BR", "recapture": "B1"},
        "AQ": {"p": "AQ", "q": "AQ", "recapture": "AQ"},
        "BQ": {"p": "BQ", "q": "BQ", "recapture": "BQ"},
        "AL": {"p": "AL", "q": "AL", "recapture": "AL"},
        "BR": {"p": "BR", "q": "BR", "recapture": "BR"},
    }
    cases.append({"name": "separable_action_different", "initial": ["A0", "B0"],
                  "outputs": outputs, "effect_envelopes": {s: ("SUBMIT_ALLOWED" if s[0] == "A" else "SUBMIT_FORBIDDEN") for s in states},
                  "transitions": delta, "unsafe_probe": "u", "unsafe_successors": {"A0": "AL", "B0": "BR"}})
    states = ("C0", "D0", "C1", "D1")
    cases.append({"name": "action_equivalent_alias", "initial": ["C0", "D0"],
                  "outputs": {s: "READY" for s in states}, "effect_envelopes": {s: "SAME_SAFE_EFFECT" for s in states},
                  "transitions": {"C0": {"p": "C1", "q": "C1", "recapture": "C0"},
                                  "D0": {"p": "D1", "q": "D1", "recapture": "D0"},
                                  "C1": {"p": "C1", "q": "C1", "recapture": "C1"},
                                  "D1": {"p": "D1", "q": "D1", "recapture": "D1"}}})
    states = ("E0", "F0", "E1", "F1", "EL", "FR")
    outputs = {s: "READY" for s in states}
    outputs.update(EL="LEFT", FR="RIGHT")
    cases.append({"name": "safe_bisimulation_impossible", "initial": ["E0", "F0"], "outputs": outputs,
                  "effect_envelopes": {s: ("EFFECT_E" if s[0] == "E" else "EFFECT_F") for s in states},
                  "transitions": {"E0": {"p": "E1", "q": "E1", "recapture": "E0"},
                                  "F0": {"p": "F1", "q": "F1", "recapture": "F0"},
                                  "E1": {"p": "E1", "q": "E1", "recapture": "E1"},
                                  "F1": {"p": "F1", "q": "F1", "recapture": "F1"},
                                  "EL": {"p": "EL", "q": "EL", "recapture": "EL"},
                                  "FR": {"p": "FR", "q": "FR", "recapture": "FR"}},
                  "unsafe_probe": "u", "unsafe_successors": {"E0": "EL", "F0": "FR"},
                  "bisimulation_relation": [["E0", "F0"], ["E1", "F1"]]})
    return cases


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def leaf(belief, case):
    env = {case["effect_envelopes"][s] for s in belief}
    status = "IDENTIFIED" if len(belief) == 1 else ("ACTION_EQUIVALENT" if len(env) == 1 else "YIELD")
    return {"kind": "leaf", "belief": sorted(belief), "disposition": status,
            "reachable_effect_envelopes": sorted(env)}


def expand(belief, depth, case):
    initial = leaf(belief, case)
    if initial["disposition"] != "YIELD" or depth == 0:
        return [initial]
    trees = [initial]
    for probe in SAFE:
        groups = {}
        for state in belief:
            dest = case["transitions"][state][probe]
            groups.setdefault(case["outputs"][dest], set()).add(dest)
        labels = sorted(groups)
        options = [expand(tuple(sorted(groups[label])), depth - 1, case) for label in labels]
        for combo in itertools.product(*options):
            trees.append({"kind": "probe", "probe": probe, "belief": sorted(belief),
                          "branches": {label: tree for label, tree in zip(labels, combo)}})
    return trees


def stats(tree, depth=0, cost=0):
    if tree["kind"] == "leaf":
        return [(depth, cost)]
    return [row for child in tree["branches"].values() for row in stats(child, depth + 1, cost + COST[tree["probe"]])]


def terminals(tree):
    if tree["kind"] == "leaf":
        return [tree["disposition"]]
    return [status for child in tree["branches"].values() for status in terminals(child)]


def run():
    cases = fixture_cases()
    fixture = {"safe_probes": list(SAFE), "cost": COST, "max_depth": DEPTH, "cases": cases}
    rows = []
    for case in cases:
        layers = []
        for depth in range(DEPTH + 1):
            trees = expand(tuple(case["initial"]), depth, case)
            valid = [tree for tree in trees if all(status != "YIELD" for status in terminals(tree))]
            def rank(tree):
                values = stats(tree)
                return max(v[0] for v in values), max(v[1] for v in values), sum(v[0] for v in values), canon(tree)
            best = min(valid, key=rank) if valid else None
            layers.append({"depth_limit": depth, "policy_tree_count": len(trees),
                           "resolved_policy_trees": len(valid),
                           "policy_tree_sha256_sorted": hashlib.sha256("\n".join(sorted(map(canon, trees))).encode()).hexdigest(),
                           "policy_trees": trees, "selected_policy": best,
                           "selected_worst_depth_and_cost": None if best is None else list(rank(best)[:2])})
        rows.append({"case": case["name"], "layers": layers})
    raw = {"allocation_id": ALLOCATION, "fixture": fixture,
           "fixture_sha256": hashlib.sha256(canon(fixture).encode()).hexdigest(),
           "result": rows, "formal_claim": "METHOD_ONLY_FINITE_FIXTURE"}
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite {OUT}")
    data = (canon(raw) + "\n").encode()
    OUT.write_bytes(data)
    print(json.dumps({"allocation_id": ALLOCATION, "raw_path": str(OUT),
                      "raw_sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}, sort_keys=True))


if __name__ == "__main__":
    run()
