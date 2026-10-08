#!/usr/bin/env python3
"""Deterministic policy-arm runner for the frozen finite epistemic-action fixture."""

import argparse
import json
from pathlib import Path


def recognize(case):
    evidence = case["initial"]
    if not evidence["decision_set"]:
        return "UNKNOWN"
    if not evidence["representation_usable"]:
        return "NEEDS_TRANSFORM"
    if evidence["complete"] and len(evidence["decision_set"]) == 1:
        return "SUFFICIENT"
    relevant = [a for a in case["actions"] if a["safe"] and a["decision_relevant"]]
    if any(a["kind"] == "ACQUIRE" for a in relevant):
        return "NEEDS_ACQUISITION"
    if any(a["kind"] == "PROBE" for a in relevant):
        return "NEEDS_PROBE"
    return "BLOCKED_EVIDENCE"


def choose_available(case):
    evidence = case["initial"]
    need = recognize(case)
    if need == "NEEDS_TRANSFORM":
        return "TRANSFORM"
    if need in ("NEEDS_ACQUISITION", "NEEDS_PROBE"):
        for action in case["actions"]:
            if action["safe"] and action["decision_relevant"] and action["kind"] == ("ACQUIRE" if need == "NEEDS_ACQUISITION" else "PROBE"):
                return action["kind"]
        return "YIELD"
    if need == "SUFFICIENT":
        # The AVAILABLE policy has a deliberate stop-cost defect: it takes a
        # safe action even when that action cannot change the decision set.
        for action in case["actions"]:
            if action["safe"]:
                return action["kind"]
        return "COMMIT"
    return "YIELD"


def action_record(case, action_kind, current):
    if action_kind in ("COMMIT", "YIELD"):
        return current
    action = next((item for item in case["actions"] if item["kind"] == action_kind), None)
    if action is None:
        return current
    return action["result"]


def run(fixture):
    rows = []
    for case in fixture["cases"]:
        for arm in fixture["arms"]:
            if arm == "PRESCRIBED":
                first = case["prescribed"]
                after = action_record(case, first, case["initial"])
                if first in ("ACQUIRE", "TRANSFORM", "PROBE") and after["complete"] and after["representation_usable"] and len(after["decision_set"]) == 1:
                    actions = [first, "COMMIT"]
                else:
                    actions = [first]
            elif arm == "AVAILABLE":
                first = choose_available(case)
                if first in ("ACQUIRE", "TRANSFORM", "PROBE"):
                    after = action_record(case, first, case["initial"])
                    if after["complete"] and after["representation_usable"] and len(after["decision_set"]) == 1:
                        actions = [first, "COMMIT"]
                    else:
                        actions = [first, "YIELD"]
                else:
                    actions = [first]
            else:
                initial = case["initial"]
                if initial["complete"] and initial["representation_usable"] and len(initial["decision_set"]) == 1:
                    actions = ["COMMIT"]
                else:
                    actions = ["YIELD"]

            evidence = case["initial"]
            action_evidence = []
            for action in actions:
                next_evidence = action_record(case, action, evidence)
                if action in ("ACQUIRE", "TRANSFORM", "PROBE"):
                    action_evidence.append({"action": action, "before": evidence, "after": next_evidence})
                evidence = next_evidence
            final = actions[-1]
            if final == "COMMIT" and evidence["complete"] and evidence["representation_usable"] and len(evidence["decision_set"]) == 1:
                decision = evidence["decision_set"][0]
            else:
                decision = "UNKNOWN"
            rows.append({
                "case_id": case["id"],
                "arm": arm,
                "recognized_need": recognize(case),
                "actions": actions,
                "evidence_before": case["initial"],
                "action_evidence": action_evidence,
                "evidence_after": evidence,
                "final_decision": decision,
                "unrelated_side_effects": [],
            })
    return {"schema": "epistemic-action-raw-v1", "allocation": fixture["allocation"], "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    print(json.dumps(run(fixture), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
