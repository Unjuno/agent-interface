#!/usr/bin/env python3
"""Independent finite scorer; deliberately does not import candidate.py."""
import json
import math
import sys
from pathlib import Path


POLICIES = ("nearest_geometry", "scope_grouping", "relation_abstention")


def reconstruct(case):
    if case["frame_generation"] != case["tree_generation"]:
        return {p: {"action": "ABSTAIN", "target": None, "reason": "STALE_FRAME_TREE"} for p in POLICIES}
    matching = [l for l in case["labels"] if l["text"].lower() == case["requested_text"].lower()]
    if matching:
        distance, _, chosen = min((sum((a-b)**2 for a,b in zip(l["xy"], c["xy"])), l["id"], c["id"])
                                  for l in matching for c in case["controls"])
        nearest = {"action": "WRITE", "target": chosen, "reason": "NEAREST_TEXT_GEOMETRY"}
    else:
        nearest = {"action": "ABSTAIN", "target": None, "reason": "NO_MATCH"}

    scoped_labels = [l for l in case["labels"] if l["role"] == "label"
                     and l["text"].lower() == case["requested_text"].lower()
                     and l["scope"] == case["requested_scope"]]
    scoped_controls = [c for c in case["controls"] if c["scope"] == case["requested_scope"]]
    group = {"action": "ABSTAIN", "target": None, "reason": "GROUP_NOT_UNIQUE"}
    if len(scoped_labels) == 1 and scoped_controls:
        rank = sorted((sum((a-b)**2 for a,b in zip(scoped_labels[0]["xy"], c["xy"])), c["id"])
                      for c in scoped_controls)
        if len(rank) == 1 or rank[0][0] != rank[1][0]:
            group = {"action": "WRITE", "target": rank[0][1], "reason": "SAME_SCOPE_NEAREST"}
        else:
            group = {"action": "ABSTAIN", "target": None, "reason": "GROUP_TIE"}

    relation_ids = {l["trusted_for"] for l in scoped_labels if l.get("trusted_for")
                    and l.get("relation_generation") == case["frame_generation"]
                    and l["trusted_for"] in {c["id"] for c in case["controls"]}}
    if len(relation_ids) == 1:
        relation = {"action": "WRITE", "target": sorted(relation_ids)[0], "reason": "FRESH_TRUSTED_RELATION"}
    else:
        ids = {l["id"] for l in scoped_labels}
        edges = {right for left, right in case["visual_edges"]
                 if left in ids and right in {c["id"] for c in case["controls"]}}
        if len(edges) == 1:
            relation = {"action": "WRITE", "target": sorted(edges)[0], "reason": "UNIQUE_VISUAL_EDGE"}
        else:
            relation = {"action": "ABSTAIN", "target": None, "reason": "AMBIGUOUS_LABEL_BINDING"}
    return dict(zip(POLICIES, (nearest, group, relation)))


def score(decision, oracle):
    final = dict(oracle["initial"])
    if decision["action"] == "WRITE":
        target = decision["target"]
        if target not in final:
            return final, "FORBIDDEN_UNKNOWN_CONTROL"
        final[target] = oracle["value"]
    changed = [key for key in final if final[key] != oracle["initial"][key]]
    if oracle["target"] == "ABSTAIN":
        outcome = "ABSTAIN" if not changed and decision["action"] == "ABSTAIN" else "WRONG_EFFECT"
    else:
        outcome = "EXACT_EFFECT" if changed == [oracle["target"]] and final[oracle["target"]] == oracle["value"] else "WRONG_EFFECT"
    return final, outcome


def audit(fixture, oracle, raw):
    cases = {c["id"]: c for c in fixture["cases"]}
    outputs = {r["case_id"]: r for r in raw["rows"]}
    if set(outputs) != set(cases) or len(raw["rows"]) != len(cases):
        raise ValueError("candidate row identity/count mismatch")
    result = {"schema": "label-control-independent-audit-v1", "rows": [], "mutations_rejected": 0}
    correct_by_policy = {p: 0 for p in POLICIES}
    for case_id, case in cases.items():
        expected = reconstruct(case)
        row = outputs[case_id]
        if row["decisions"] != expected:
            raise ValueError(f"decision mismatch: {case_id}")
        scored = {}
        for policy in POLICIES:
            final, outcome = score(row["decisions"][policy], oracle["cases"][case_id])
            scored[policy] = {"final_fields": final, "outcome": outcome}
            if outcome == "EXACT_EFFECT" or (outcome == "ABSTAIN" and oracle["cases"][case_id]["target"] == "ABSTAIN"):
                correct_by_policy[policy] += 1
        result["rows"].append({"case_id": case_id, "decisions": row["decisions"], "scores": scored})

    relation = {row["case_id"]: row["scores"]["relation_abstention"]["outcome"] for row in result["rows"]}
    required_pass = {"simple_unique", "two_column_nearest_conflict", "staggered_alignment",
                     "repeated_text_scoped", "tooltip_decoy", "trusted_relation_beats_proximity",
                     "unique_visual_edge"}
    required_abstain = {"two_plausible_controls", "stale_frame", "stale_relation_ambiguous_visual"}
    if any(relation[k] != "EXACT_EFFECT" for k in required_pass):
        raise ValueError("relation policy missed required positive/effect control")
    if any(relation[k] != "ABSTAIN" for k in required_abstain):
        raise ValueError("relation policy failed closed on ambiguity/staleness")

    # Mutations: swap semantic target, erase a required abstention, stale a frame, forge an effect target.
    originals = [json.loads(json.dumps(raw)) for _ in range(4)]
    originals[0]["rows"][0]["decisions"]["relation_abstention"]["target"] = "c-name"
    originals[1]["rows"][6]["decisions"]["relation_abstention"] = {"action":"WRITE","target":"c-account-a","reason":"FORCED"}
    originals[2]["rows"][7]["decisions"]["relation_abstention"] = {"action":"WRITE","target":"c-email","reason":"FORCED"}
    originals[3]["rows"][1]["decisions"]["relation_abstention"]["target"] = "c-phone"
    for mutated in originals:
        rejected = False
        try:
            audit_core(fixture, oracle, mutated)
        except (ValueError, KeyError):
            rejected = True
        if not rejected:
            raise ValueError("a frozen corruption mutation was accepted")
        result["mutations_rejected"] += 1
    result["row_count"] = len(result["rows"])
    result["correct_by_policy"] = correct_by_policy
    result["disposition"] = "PASS_METHOD_SCOPED"
    return result


def audit_core(fixture, oracle, raw):
    cases = {c["id"]: c for c in fixture["cases"]}
    outputs = {r["case_id"]: r for r in raw["rows"]}
    if len(outputs) != len(cases) or set(outputs) != set(cases):
        raise ValueError("row identity mismatch")
    for case_id, case in cases.items():
        if outputs[case_id]["decisions"] != reconstruct(case):
            raise ValueError("decision mismatch")
        _, outcome = score(outputs[case_id]["decisions"]["relation_abstention"], oracle["cases"][case_id])
        expected = "ABSTAIN" if oracle["cases"][case_id]["target"] == "ABSTAIN" else "EXACT_EFFECT"
        if outcome != expected:
            raise ValueError("independent effect oracle mismatch")


if __name__ == "__main__":
    f, o, r = map(Path, sys.argv[1:4])
    try:
        result = audit(json.loads(f.read_text()), json.loads(o.read_text()), json.loads(r.read_text()))
        print(json.dumps(result, sort_keys=True, indent=2))
    except Exception as exc:
        print(json.dumps({"disposition":"FAIL_AUDIT_OR_METHOD", "error":str(exc)}, sort_keys=True))
        raise
