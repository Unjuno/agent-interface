#!/usr/bin/env python3
"""Deterministic finite simulator for Issue #9004 T0; no actuation."""
import json
import sys
from pathlib import Path

ARMS = ("always_wait", "system1_only", "agreement_only", "agreement_lease")


def execute(case, arm, lease):
    revoked = case["revocation"] is not None
    if not case["release_ok"]:
        return {"actions": [], "decision_ticks": [], "stop": "release_failure", "release_required": True,
                "release_ok": False, "effect_correct": True}
    if arm == "always_wait":
        if revoked or case["s2"] != case["truth"]:
            return {"actions": [], "decision_ticks": [], "stop": "wait_or_gate", "release_required": True,
                    "release_ok": True, "effect_correct": True}
        return {"actions": [case["s2"], case["s2"]], "decision_ticks": [case["s2_delay"], case["s2_delay"] + 1],
                "stop": "complete", "release_required": True, "release_ok": True, "effect_correct": True}
    if arm == "system1_only":
        selected = [] if revoked else [a for a in case["s1"][:lease["max_actions"]] if a == case["truth"]]
        return {"actions": selected, "decision_ticks": list(range(len(selected))),
                "stop": "revoked_or_gate" if revoked or len(selected) < len(case["s1"][:lease["max_actions"]]) else "complete",
                "release_required": True, "release_ok": True, "effect_correct": True}
    if not case["agreement"] or revoked:
        return {"actions": [], "decision_ticks": [], "stop": "yield", "release_required": True,
                "release_ok": True, "effect_correct": True}
    if arm == "agreement_only":
        action = case["s1"][0]
        allowed = action == case["truth"] and action != "commit"
        return {"actions": [action] if allowed else [], "decision_ticks": [0] if allowed else [],
                "stop": "complete" if allowed else "independent_gate", "release_required": True,
                "release_ok": True, "effect_correct": True}
    selected = []
    for tick, action in enumerate(case["s1"][:lease["max_actions"]]):
        if tick > lease["max_ticks"] or action != case["truth"] or action == "commit":
            break
        selected.append((action, tick))
    return {"actions": [a for a, _ in selected], "decision_ticks": [t for _, t in selected],
            "stop": "complete" if len(selected) == lease["max_actions"] else "lease_or_independent_gate",
            "release_required": True, "release_ok": True, "effect_correct": True}


def run(cases):
    rows = []
    for case in cases["cases"]:
        for arm in ARMS:
            rows.append({"case_id": case["id"], "arm": arm, **execute(case, arm, cases["lease"])})
    return {"schema": "agreement-continuation-raw-v1", "claims": {"live_actuation": False, "synthetic_timing": True}, "rows": rows}


if __name__ == "__main__":
    input_path, output_path = map(Path, sys.argv[1:3])
    output_path.write_text(json.dumps(run(json.loads(input_path.read_text())), indent=2, sort_keys=True) + "\n")
