"""Finite candidate policy table for model-ambiguity lifetime decision T0b."""
import itertools
import json
import sys
from pathlib import Path

LIFETIMES = ("FULL", "ZERO", "EVENT")
PHASES = ("PRE_EVENT", "POST_EVENT")
EVIDENCE = ("VALID_0", "VALID_1", "MISSING", "STALE")
ORDERS = ("NATURE_FIRST_PUBLIC", "AGENT_FIRST_REACTIVE")


def support(lifetime, phase, evidence):
    if lifetime == "FULL" and evidence.startswith("VALID_"):
        return [int(evidence[-1])]
    if lifetime == "EVENT" and phase == "POST_EVENT" and evidence.startswith("VALID_"):
        return [int(evidence[-1])]
    return [0, 1]


def action_for(theta):
    return "A" if theta == 0 else "B"


def main(path):
    rows = []
    for life, phase, evidence, order in itertools.product(LIFETIMES, PHASES, EVIDENCE, ORDERS):
        prior_support = support(life, phase, evidence)
        if order == "NATURE_FIRST_PUBLIC":
            # Nature's current choice is public before the proposed action.
            current_theta = prior_support[0]
            decision, action, reached = "CONTINUE", action_for(current_theta), [current_theta]
        elif len(prior_support) == 1:
            current_theta = prior_support[0]
            decision, action, reached = "CONTINUE", action_for(current_theta), [current_theta]
        else:
            current_theta = None
            decision, action, reached = "YIELD", None, []

        # A lifetime-unspecified robust comparator forgets the persistence rule.
        unspecified = "CONTINUE" if order == "NATURE_FIRST_PUBLIC" else "YIELD"
        # Unsafe point comparator always acts on the last valid receipt (or 0).
        point = int(evidence[-1]) if evidence.startswith("VALID_") else 0
        point_action = action_for(point)
        point_unsafe_possible = any(point != theta for theta in prior_support)
        rows.append({
            "lifetime": life, "phase": phase, "evidence": evidence, "order": order,
            "prior_support": prior_support, "decision": decision, "action": action,
            "reachable_theta": reached, "unsafe_dispatch": False,
            "unspecified_decision": unspecified,
            "point_action": point_action,
            "point_unsafe_possible": point_unsafe_possible,
        })
    controls = [{"lifetime": life, "order": order, "decision": "CONTINUE",
                 "action": "SAFE_INDEPENDENT_OF_THETA", "unsafe_dispatch": False}
                for life, order in itertools.product(LIFETIMES, ORDERS)]
    obj = {"schema": "issue-6580-t0b-candidate-v1", "rows": rows,
           "negative_controls": controls}
    Path(path).write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
