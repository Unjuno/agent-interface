#!/usr/bin/env python3
"""Emit three synthetic label-to-control proposals; no hidden oracle is read."""
import json
import math
import sys
from pathlib import Path


def choose_nearest(case):
    matches = [x for x in case["labels"] if x["text"].casefold() == case["requested_text"].casefold()]
    if not matches:
        return None, "NO_MATCH"
    pairs = [(math.dist(label["xy"], control["xy"]), label["id"], control["id"])
             for label in matches for control in case["controls"]]
    _, _, control_id = min(pairs)
    return control_id, "NEAREST_TEXT_GEOMETRY"


def choose_grouping(case):
    labels = [x for x in case["labels"] if x["role"] == "label"
              and x["text"].casefold() == case["requested_text"].casefold()
              and x["scope"] == case["requested_scope"]]
    controls = [x for x in case["controls"] if x["scope"] == case["requested_scope"]]
    if len(labels) != 1 or len(controls) == 0:
        return None, "GROUP_NOT_UNIQUE"
    ranked = sorted((math.dist(labels[0]["xy"], c["xy"]), c["id"]) for c in controls)
    if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
        return None, "GROUP_TIE"
    return ranked[0][1], "SAME_SCOPE_NEAREST"


def choose_relation(case):
    labels = [x for x in case["labels"] if x["role"] == "label"
              and x["text"].casefold() == case["requested_text"].casefold()
              and x["scope"] == case["requested_scope"]]
    controls = {x["id"] for x in case["controls"]}
    explicit = {x["trusted_for"] for x in labels
                if x.get("trusted_for") in controls
                and x.get("relation_generation") == case["frame_generation"]}
    if len(explicit) == 1:
        return next(iter(explicit)), "FRESH_TRUSTED_RELATION"
    label_ids = {x["id"] for x in labels}
    visual = {edge[1] for edge in case["visual_edges"] if edge[0] in label_ids and edge[1] in controls}
    if len(visual) == 1:
        return next(iter(visual)), "UNIQUE_VISUAL_EDGE"
    return None, "AMBIGUOUS_LABEL_BINDING"


def decide(case, policy):
    if case["frame_generation"] != case["tree_generation"]:
        return {"action": "ABSTAIN", "target": None, "reason": "STALE_FRAME_TREE"}
    fn = {"nearest_geometry": choose_nearest,
          "scope_grouping": choose_grouping,
          "relation_abstention": choose_relation}[policy]
    target, reason = fn(case)
    if target is None:
        return {"action": "ABSTAIN", "target": None, "reason": reason}
    return {"action": "WRITE", "target": target, "reason": reason}


def run(fixture):
    rows = []
    for case in fixture["cases"]:
        rows.append({"case_id": case["id"], "decisions": {
            name: decide(case, name) for name in
            ("nearest_geometry", "scope_grouping", "relation_abstention")}})
    return {"schema": "label-control-candidate-raw-v1", "rows": rows}


if __name__ == "__main__":
    print(json.dumps(run(json.loads(Path(sys.argv[1]).read_text())), sort_keys=True, separators=(",", ":")))
