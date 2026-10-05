#!/usr/bin/env python3
"""Finite sensitivity enumerator over public traces, segmentations and link sets."""
import argparse
import json
from pathlib import Path


def evaluate_combo(scenario, combo):
    records = scenario["raw_records"]
    mapping = scenario["segmentations"][combo["segmentation"]]
    record_ids = {r["record_id"] for r in records}
    if set(mapping) != record_ids:
        raise ValueError("segmentation must assign each observed raw record exactly once")
    channels = {r["record_id"]: r["channel"] for r in records}
    nodes = sorted({f"{channels[rid]}:{unit}" for rid, unit in mapping.items()})
    parent = {node: node for node in nodes}
    members = {node: {node} for node in nodes}

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    accepted, rejected = [], []
    edges = scenario["linkage_sets"][combo["linkage"]][combo["segmentation"]]
    for e in edges:
        left, right = e["left"], e["right"]
        if left not in parent or right not in parent or left.split(":", 1)[0] == right.split(":", 1)[0]:
            rejected.append(e["edge_id"])
            continue
        a, b = find(left), find(right)
        ca = {n.split(":", 1)[0] for n in members[a]}
        cb = {n.split(":", 1)[0] for n in members[b]}
        if a != b and ca & cb:
            rejected.append(e["edge_id"])
            continue
        if a != b:
            root, child = sorted((a, b))
            parent[child] = root
            members[root] |= members.pop(child)
        accepted.append(e["edge_id"])

    groups = {}
    for node in nodes:
        root = find(node)
        groups.setdefault(root, []).append(node)
    group_rows = []
    histogram = {}
    for root, group_nodes in sorted(groups.items()):
        channels_in_group = sorted(n.split(":", 1)[0] for n in group_nodes)
        width = len(channels_in_group)
        histogram[str(width)] = histogram.get(str(width), 0) + 1
        group_rows.append({"nodes": sorted(group_nodes), "channels": channels_in_group, "channel_count": width})
    overlap = sum(n for width, n in histogram.items() if int(width) >= 2)
    return {"combination_id": combo["id"], "segmentation_id": combo["segmentation"],
            "linkage_id": combo["linkage"], "raw_record_count": len(records),
            "observed_linkage_component_count": len(nodes) - len(accepted),
            "capture_history_histogram": histogram, "multi_channel_overlap_count": overlap,
            "decision": "AT_OR_ABOVE_THRESHOLD" if overlap >= scenario["decision_threshold_multi_channel"] else "BELOW_THRESHOLD",
            "accepted_edge_ids": sorted(accepted), "rejected_conflict_edge_ids": sorted(rejected),
            "groups": group_rows, "censored_record_ids": sorted(r["record_id"] for r in records if r["right_censored"]),
            "missing_intervals": scenario["missing_intervals"],
            "all_channel_unobserved_status": "NOT_ESTIMATED"}


def summarize_set(scenario, runs, combination_ids):
    chosen = [r for r in runs if r["combination_id"] in combination_ids]
    values = [r["multi_channel_overlap_count"] for r in chosen]
    low, high = min(values), max(values)
    threshold = scenario["decision_threshold_multi_channel"]
    if low < threshold <= high:
        decision = "UNIDENTIFIED"
    elif low >= threshold:
        decision = "AT_OR_ABOVE_THRESHOLD"
    else:
        decision = "BELOW_THRESHOLD"
    return {"combination_ids": combination_ids, "values": values, "lower": low, "upper": high,
            "threshold": threshold, "decision": decision, "flagged": decision == "UNIDENTIFIED"}


def evaluate(data):
    scenarios = []
    for scenario in data["scenarios"]:
        runs = [evaluate_combo(scenario, c) for c in scenario["combinations"]]
        summaries = {key: summarize_set(scenario, runs, ids)
                     for key, ids in scenario["analysis_sets"].items()}
        interaction = None
        if {"boundary_only", "linkage_only", "joint"} <= set(summaries):
            b, l, j = (summaries[x] for x in ("boundary_only", "linkage_only", "joint"))
            interaction = {"boundary_width": b["upper"] - b["lower"],
                           "linkage_width": l["upper"] - l["lower"],
                           "joint_width": j["upper"] - j["lower"],
                           "joint_changes_decision_without_one_factor":
                               j["decision"] == "UNIDENTIFIED" and b["decision"] != "UNIDENTIFIED"
                               and l["decision"] != "UNIDENTIFIED"}
        scenarios.append({"scenario_id": scenario["scenario_id"], "source_dependence_groups": scenario["source_dependence_groups"], "combinations": runs,
                          "analysis_sets": summaries, "joint_interaction": interaction})
    return {"protocol": "issue-8004-t0-a02-v1", "scenario_count": len(scenarios),
            "scenarios": scenarios, "population_size_estimate": None,
            "all_channel_unobserved_count_estimate": None,
            "scope": "Finite authored assignment sensitivity only; no posterior probability or live failure-rate estimate."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = evaluate(json.loads(Path(args.input).read_text()))
    Path(args.output).write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
