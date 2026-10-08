#!/usr/bin/env python3
"""Enumerate safe adaptive observation trees and terminal-effect envelopes."""
import hashlib
import itertools
import json
from pathlib import Path

ALLOCATION = "AI-6147-T0-20261003-04"
SAFE = ("p", "q", "recapture")
COST = {name: 1 for name in SAFE}
MAX_DEPTH = 2
OUTPUT = Path(__file__).with_name("RAW.json")


def machines():
    fixtures = []
    # A/B are safely distinguishable, but both probes invalidate the old target.
    fixtures.append({
        "name": "separates_initial_but_stales_terminal_action",
        "initial": ["A0", "B0"],
        "outputs": {"A0":"READY","B0":"READY","A1":"READY","B1":"READY","A2":"LEFT","B2":"RIGHT","AU":"LEFT","BU":"RIGHT"},
        "effect_envelopes": {"A0":"OLD_TARGET_ALLOWED_A","B0":"OLD_TARGET_FORBIDDEN_B","A1":"MOVED_TARGET_A_FORBIDDEN","B1":"MOVED_TARGET_B_FORBIDDEN","A2":"STALE_TARGET_A_FORBIDDEN","B2":"STALE_TARGET_B_FORBIDDEN"},
        "transitions": {"A0":{"p":"A1","q":"A1","recapture":"A0"},"B0":{"p":"B1","q":"B1","recapture":"B0"},
                        "A1":{"p":"A1","q":"A2","recapture":"A1"},"B1":{"p":"B1","q":"B2","recapture":"B1"},
                        "A2":{"p":"A2","q":"A2","recapture":"A2"},"B2":{"p":"B2","q":"B2","recapture":"B2"}},
        "unsafe_probe":"u","unsafe_transitions":{"A0":"AU","B0":"BU"},"allowed_effect_envelopes":["CURRENT_TARGET_ALLOWED"]}),
    # Distinct initial identities converge to one current terminal state.
    fixtures.append({
        "name": "unidentified_initial_converges_to_safe_terminal",
        "initial": ["C0", "D0"],
        "outputs": {"C0":"READY","D0":"READY","Z":"READY"},
        "effect_envelopes": {"C0":"OLD_C_ONLY","D0":"OLD_D_ONLY","Z":"CURRENT_TARGET_ALLOWED"},
        "transitions": {"C0":{"p":"Z","q":"C0","recapture":"C0"},"D0":{"p":"Z","q":"D0","recapture":"D0"},
                        "Z":{"p":"Z","q":"Z","recapture":"Z"}},
        "allowed_effect_envelopes":["CURRENT_TARGET_ALLOWED"]}),
    # Action-equivalent aliases require no probe and do not imply identity.
    fixtures.append({
        "name": "initial_action_equivalent_without_identity",
        "initial": ["I0", "J0"],
        "outputs": {"I0":"READY","J0":"READY"},
        "effect_envelopes": {"I0":"CURRENT_TARGET_ALLOWED","J0":"CURRENT_TARGET_ALLOWED"},
        "transitions": {"I0":{"p":"I0","q":"I0","recapture":"I0"},"J0":{"p":"J0","q":"J0","recapture":"J0"}},
        "allowed_effect_envelopes":["CURRENT_TARGET_ALLOWED"]}),
    # Safe probes preserve an output-invariant relation; unsafe u distinguishes.
    fixtures.append({
        "name": "action_different_safe_bisimulation",
        "initial": ["E0", "F0"],
        "outputs": {"E0":"READY","F0":"READY","E1":"READY","F1":"READY","EU":"LEFT","FU":"RIGHT"},
        "effect_envelopes": {"E0":"EFFECT_E","F0":"EFFECT_F","E1":"EFFECT_E","F1":"EFFECT_F"},
        "transitions": {"E0":{"p":"E1","q":"E1","recapture":"E0"},"F0":{"p":"F1","q":"F1","recapture":"F0"},
                        "E1":{"p":"E1","q":"E1","recapture":"E1"},"F1":{"p":"F1","q":"F1","recapture":"F1"}},
        "unsafe_probe":"u","unsafe_transitions":{"E0":"EU","F0":"FU"},
        "bisimulation_relation":[["E0","F0"],["E1","F1"]],"allowed_effect_envelopes":["CURRENT_TARGET_ALLOWED"]})
    return fixtures


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def leaf(belief, case):
    envelopes = sorted({case["effect_envelopes"][state] for state in belief})
    if len(belief) == 1:
        epistemic = "CURRENT_TERMINAL_SINGLETON"
    elif len(envelopes) == 1:
        epistemic = "ACTION_EQUIVALENT_CURRENT"
    else:
        epistemic = "AMBIGUOUS_CURRENT"
    admitted = set(envelopes) <= set(case["allowed_effect_envelopes"])
    return {"kind":"leaf","terminal_states":sorted(belief),"terminal_effect_envelopes":envelopes,
            "epistemic_status":epistemic,"initial_identity_claim":False,
            "terminal_decision":"ALLOW_SCOPED_EFFECT" if admitted else "YIELD_OR_REOBSERVE"}


def trees(belief, depth, case):
    node = leaf(belief, case)
    if node["epistemic_status"] != "AMBIGUOUS_CURRENT" or depth == 0:
        return [node]
    result = [node]
    for probe in SAFE:
        partition = {}
        for state in belief:
            nxt = case["transitions"][state][probe]
            partition.setdefault(case["outputs"][nxt], set()).add(nxt)
        labels = sorted(partition)
        options = [trees(tuple(sorted(partition[label])), depth - 1, case) for label in labels]
        for selection in itertools.product(*options):
            result.append({"kind":"probe","probe":probe,"belief":sorted(belief),
                           "branches":{label:child for label,child in zip(labels,selection)}})
    return result


def terminal_rows(tree, depth=0, cost=0):
    if tree["kind"] == "leaf":
        return [{"depth":depth,"cost":cost,"states":tree["terminal_states"],
                 "effects":tree["terminal_effect_envelopes"],"epistemic":tree["epistemic_status"],
                 "decision":tree["terminal_decision"],"initial_identity_claim":tree["initial_identity_claim"]}]
    return [row for child in tree["branches"].values() for row in terminal_rows(child,depth+1,cost+COST[tree["probe"]])]


def flatten_status(tree):
    if tree["kind"] == "leaf":
        return [tree["epistemic_status"]]
    return [value for child in tree["branches"].values() for value in flatten_status(child)]


def run():
    cases = machines()
    spec = {"safe_probes":list(SAFE),"cost":COST,"max_depth":MAX_DEPTH,"cases":cases}
    results=[]
    for case in cases:
        layers=[]
        for depth in range(MAX_DEPTH+1):
            all_trees=trees(tuple(case["initial"]),depth,case)
            complete=[t for t in all_trees if "AMBIGUOUS_CURRENT" not in flatten_status(t)]
            def rank(tree):
                rows=terminal_rows(tree)
                return max(row["depth"] for row in rows),max(row["cost"] for row in rows),sum(row["depth"] for row in rows),canonical(tree)
            choice=min(complete,key=rank) if complete else None
            layers.append({"depth_limit":depth,"tree_count":len(all_trees),"resolved_tree_count":len(complete),
                           "trees_sha256_sorted":hashlib.sha256("\n".join(sorted(map(canonical,all_trees))).encode()).hexdigest(),
                           "trees":all_trees,"selected":choice,
                           "selected_terminal_rows":[] if choice is None else terminal_rows(choice)})
        results.append({"case":case["name"],"layers":layers})
    raw={"allocation_id":ALLOCATION,"spec":spec,"spec_sha256":hashlib.sha256(canonical(spec).encode()).hexdigest(),
         "results":results,"claim":"FINITE_SYNTHETIC_METHOD_ONLY"}
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to overwrite {OUTPUT}")
    data=(canonical(raw)+"\n").encode()
    OUTPUT.write_bytes(data)
    print(json.dumps({"allocation_id":ALLOCATION,"raw":OUTPUT.name,"bytes":len(data),
                      "sha256":hashlib.sha256(data).hexdigest()},sort_keys=True))


if __name__ == "__main__":
    run()
