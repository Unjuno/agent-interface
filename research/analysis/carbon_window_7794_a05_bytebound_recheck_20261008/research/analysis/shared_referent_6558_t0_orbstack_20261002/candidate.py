#!/usr/bin/env python3
"""Finite candidate policies for Issue #6558. No GUI, model, or input."""
import json
import pathlib
import sys


def run_case(case):
    initial = next(x for x in case["initial_items"] if x["object"] == case["initial_ack_object"])
    current_by_node = {x["node"]: x for x in case["current_items"]}
    initial_node = initial["node"]
    changed = case["current_generation"] != case["initial_generation"]
    # D: re-ground only on a referent-changing event; reject missing/stale evidence.
    if case["event"] in {"sort-rebind", "virtual-reuse", "app-update"}:
        response_property = case["response_property"]
        matches = [item["object"] for item in case["current_items"] if response_property in item["properties"]]
        if (not response_property or case["response_generation"] != case["current_generation"] or len(matches) != 1):
            scoped = None
            scoped_reason = "UNKNOWN_INVALID_RESTATEMENT"
        else:
            scoped = matches[0]
            scoped_reason = "REGROUNDED"
    else:
        scoped = case["initial_ack_object"]
        scoped_reason = "UNCHANGED_REFERENT" if not changed else "BENIGN_TRANSFORM"
    # A: stale screen coordinate/slot.
    raw = case["current_items"][case["initial_slot"]]["object"]
    # B: fresh machine binding to the DOM node selected at acknowledgment.
    bound = current_by_node[initial_node]["object"]
    # C: initial clarification only; acknowledgment remains bound to the old node.
    clarified = current_by_node[initial_node]["object"]
    return {
        "case_id": case["id"],
        "raw_coordinate": {"object": raw, "asks": 0},
        "fresh_machine_rebind": {"object": bound, "asks": 0},
        "initial_clarification_only": {"object": clarified, "asks": 1 if case["id"] == "ambiguous-initial-clarified" else 0},
        "scoped_restatement": {"object": scoped, "asks": 1 if scoped_reason == "REGROUNDED" else 0, "reason": scoped_reason},
        "authority_granted_by_cue": False,
    }


def main():
    fixture = json.loads(pathlib.Path(sys.argv[1]).read_text())
    rows = [run_case(c) for c in fixture["cases"]]
    pathlib.Path(sys.argv[2]).write_text(json.dumps({"schema":"shared-referent-candidate-v1","rows":rows}, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status":"CANDIDATE_COMPLETE","rows":len(rows)}))


if __name__ == "__main__":
    main()
