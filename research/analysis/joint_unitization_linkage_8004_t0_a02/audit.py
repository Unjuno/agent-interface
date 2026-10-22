#!/usr/bin/env python3
"""Independent exhaustive audit; no import or execution of candidate.py."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent


def make_nodes(scenario, seg_id):
    records = scenario["raw_records"]
    raw_ids = {r["record_id"] for r in records}
    mapping = scenario["segmentations"][seg_id]
    if set(mapping) != raw_ids:
        raise ValueError("segmentation raw-record coverage mismatch")
    channels = {r["record_id"]: r["channel"] for r in records}
    return sorted({f"{channels[rid]}:{unit}" for rid, unit in mapping.items()})


def components_for(nodes, edges):
    """Choose maximum-cardinality channel-unique linkage independently by exhaustive search."""
    best_edges = None
    best_key = None
    for mask in range(1 << len(edges)):
        subset = [e for i, e in enumerate(edges) if (mask >> i) & 1]
        adjacency = {node: set() for node in nodes}
        valid = True
        for edge in subset:
            left, right = edge["left"], edge["right"]
            if left not in adjacency or right not in adjacency:
                valid = False
                break
            adjacency[left].add(right); adjacency[right].add(left)
        if not valid:
            continue
        groups = []
        unseen = set(nodes)
        while unseen:
            seed = min(unseen); stack = [seed]; group = set()
            while stack:
                node = stack.pop()
                if node in group:
                    continue
                group.add(node); unseen.discard(node)
                stack.extend(adjacency[node] - group)
            channel_names = [x.split(":", 1)[0] for x in group]
            if len(channel_names) != len(set(channel_names)):
                valid = False
                break
            groups.append(sorted(group))
        if not valid:
            continue
        ids = tuple(sorted(e["edge_id"] for e in subset))
        key = (-len(subset), ids)
        if best_key is None or key < best_key:
            best_key, best_edges = key, list(ids)
    if best_edges is None:
        raise ValueError("no valid linkage assignment")
    return best_edges


def combo_result(scenario, combo):
    nodes = make_nodes(scenario, combo["segmentation"])
    edges = scenario["linkage_sets"][combo["linkage"]][combo["segmentation"]]
    accepted = components_for(nodes, edges)
    chosen = set(accepted)
    adjacency = {node: set() for node in nodes}
    for edge in edges:
        if edge["edge_id"] in chosen:
            adjacency[edge["left"]].add(edge["right"]); adjacency[edge["right"]].add(edge["left"])
    groups = []
    unseen = set(nodes)
    while unseen:
        seed = min(unseen); stack = [seed]; group = set()
        while stack:
            node = stack.pop()
            if node in group:
                continue
            group.add(node); unseen.discard(node)
            stack.extend(adjacency[node] - group)
        member_nodes = sorted(group)
        channel_names = sorted(x.split(":", 1)[0] for x in member_nodes)
        groups.append({"nodes": member_nodes, "channels": channel_names, "channel_count": len(channel_names)})
    groups.sort(key=lambda x: x["nodes"])
    histogram = {}
    for group in groups:
        key = str(group["channel_count"])
        histogram[key] = histogram.get(key, 0) + 1
    overlap = sum(value for key, value in histogram.items() if int(key) >= 2)
    proposed = {e["edge_id"] for e in edges}
    return {"combination_id": combo["id"], "segmentation_id": combo["segmentation"],
            "linkage_id": combo["linkage"], "raw_record_count": len(scenario["raw_records"]),
            "observed_linkage_component_count": len(nodes) - len(accepted),
            "capture_history_histogram": histogram, "multi_channel_overlap_count": overlap,
            "decision": "AT_OR_ABOVE_THRESHOLD" if overlap >= scenario["decision_threshold_multi_channel"] else "BELOW_THRESHOLD",
            "accepted_edge_ids": accepted, "rejected_conflict_edge_ids": sorted(proposed - chosen),
            "groups": groups,
            "censored_record_ids": sorted(r["record_id"] for r in scenario["raw_records"] if r["right_censored"]),
            "missing_intervals": scenario["missing_intervals"],
            "all_channel_unobserved_status": "NOT_ESTIMATED"}


def envelope(scenario, results, combo_ids):
    rows = [x for x in results if x["combination_id"] in combo_ids]
    if len(rows) != len(combo_ids):
        raise ValueError("analysis set refers to absent combination")
    values = [x["multi_channel_overlap_count"] for x in rows]
    lower, upper = min(values), max(values)
    threshold = scenario["decision_threshold_multi_channel"]
    if lower < threshold <= upper:
        decision = "UNIDENTIFIED"
    elif lower >= threshold:
        decision = "AT_OR_ABOVE_THRESHOLD"
    else:
        decision = "BELOW_THRESHOLD"
    return {"combination_ids": combo_ids, "values": values, "lower": lower, "upper": upper,
            "threshold": threshold, "decision": decision, "flagged": decision == "UNIDENTIFIED"}


def expected_output(public):
    output_scenarios = []
    for scenario in public["scenarios"]:
        runs = [combo_result(scenario, combo) for combo in scenario["combinations"]]
        summaries = {name: envelope(scenario, runs, ids) for name, ids in scenario["analysis_sets"].items()}
        interaction = None
        if {"boundary_only", "linkage_only", "joint"} <= set(summaries):
            b, l, j = (summaries[x] for x in ("boundary_only", "linkage_only", "joint"))
            interaction = {"boundary_width": b["upper"] - b["lower"],
                           "linkage_width": l["upper"] - l["lower"],
                           "joint_width": j["upper"] - j["lower"],
                           "joint_changes_decision_without_one_factor": j["decision"] == "UNIDENTIFIED"
                               and b["decision"] != "UNIDENTIFIED" and l["decision"] != "UNIDENTIFIED"}
        output_scenarios.append({"scenario_id": scenario["scenario_id"], "source_dependence_groups": scenario["source_dependence_groups"], "combinations": runs,
                                 "analysis_sets": summaries, "joint_interaction": interaction})
    return {"protocol": "issue-8004-t0-a02-v1", "scenario_count": len(output_scenarios),
            "scenarios": output_scenarios, "population_size_estimate": None,
            "all_channel_unobserved_count_estimate": None,
            "scope": "Finite authored assignment sensitivity only; no posterior probability or live failure-rate estimate."}


def validate_truth(public, truth):
    if {x["scenario_id"] for x in public["scenarios"]} != {x["scenario_id"] for x in truth["scenarios"]}:
        raise ValueError("truth scenario frame mismatch")
    pub_by_id = {x["scenario_id"]: x for x in public["scenarios"]}
    summaries = {}
    for oracle in truth["scenarios"]:
        scenario = pub_by_id[oracle["scenario_id"]]
        records = {r["record_id"]: r for r in scenario["raw_records"]}
        if set(oracle["record_to_event"]) != set(records):
            raise ValueError("oracle/raw record coverage mismatch")
        event_ids = {x["event_id"] for x in oracle["latent_events"]}
        if set(oracle["record_to_event"].values()) - event_ids:
            raise ValueError("record references unknown latent event")
        for event in oracle["latent_events"]:
            eid = event["event_id"]
            statuses = event["channel_status"]
            if set(statuses) != set(scenario["channels"]):
                raise ValueError("channel status denominator mismatch")
            associated = [rid for rid, eid0 in oracle["record_to_event"].items() if eid0 == eid]
            for channel in scenario["channels"]:
                channel_records = [rid for rid in associated if records[rid]["channel"] == channel]
                status = statuses[channel]
                if status in ("CAPTURED", "RIGHT_CENSORED_CAPTURED"):
                    if len(channel_records) != 1:
                        raise ValueError("capture/status mismatch")
                    if (status == "RIGHT_CENSORED_CAPTURED") != bool(records[channel_records[0]]["right_censored"]):
                        raise ValueError("censor/status mismatch")
                elif status in ("OBSERVED_ZERO", "MISSING") and channel_records:
                    raise ValueError("noncapture has a source record")
                if status == "MISSING":
                    intervals = [i for i in scenario["missing_intervals"] if i["channel"] == channel]
                    other_records = [records[rid] for rid in associated]
                    if not any(any(i["start"] <= rr["start"] and rr["end"] <= i["end"] for i in intervals)
                               for rr in other_records):
                        raise ValueError("missing status lacks aligned missing interval")
        cap_counts = {ch: sum(1 for e in oracle["latent_events"] if e["channel_status"][ch] in ("CAPTURED", "RIGHT_CENSORED_CAPTURED"))
                      for ch in scenario["channels"]}
        summaries[oracle["scenario_id"]] = {"latent_event_count": len(oracle["latent_events"]),
            "all_channel_unobserved_truth_count": sum(all(v == "OBSERVED_ZERO" for v in e["channel_status"].values())
                                                       for e in oracle["latent_events"]),
            "captured_opportunities_by_channel": cap_counts}
    for scenario_id in ("joint_boundary_linkage_independent_sources", "joint_boundary_linkage_shared_AB"):
        main = pub_by_id[scenario_id]
        main_oracle = next(x for x in truth["scenarios"] if x["scenario_id"] == scenario_id)
        ids = main_oracle["record_to_event"]
        if ids["b_overlap"] == ids["c_overlap"]:
            raise ValueError("overlapping cascade control must be two distinct events")
        if not any(i["channel"] == "D" and i["start"] <= 50 and 52 <= i["end"] for i in main["missing_intervals"]):
            raise ValueError("missing-telemetry control absent")
        if not any(r["right_censored"] for r in main["raw_records"]):
            raise ValueError("right-censored control absent")
        if set(main["source_dependence_groups"]) != set(main["channels"]):
            raise ValueError("source-dependence assignment incomplete")
    if (pub_by_id["joint_boundary_linkage_independent_sources"]["source_dependence_groups"]
            == pub_by_id["joint_boundary_linkage_shared_AB"]["source_dependence_groups"]):
        raise ValueError("source-dependence sensitivity controls were not varied")
    return summaries


def validate(public, truth, got):
    oracle_summary = validate_truth(public, truth)
    expected = expected_output(public)
    if got != expected:
        raise AssertionError("candidate output differs from independent exhaustive reconstruction")
    clean = next(x for x in expected["scenarios"] if x["scenario_id"] == "clean_unique_ids")
    if clean["analysis_sets"]["clean"]["lower"] != 3 or clean["analysis_sets"]["clean"]["upper"] != 3:
        raise AssertionError("unique-ID clean control failed to recover oracle overlap")
    for scenario_id in ("joint_boundary_linkage_independent_sources", "joint_boundary_linkage_shared_AB"):
        joint = next(x for x in expected["scenarios"] if x["scenario_id"] == scenario_id)
        b, l, j = (joint["analysis_sets"][x] for x in ("boundary_only", "linkage_only", "joint"))
        if b["lower"] != b["upper"] or l["lower"] != l["upper"]:
            raise AssertionError("one-factor controls unexpectedly vary")
        if not joint["joint_interaction"]["joint_changes_decision_without_one_factor"]:
            raise AssertionError("joint ambiguity did not uniquely cross the threshold")
        if j["decision"] != "UNIDENTIFIED" or j["lower"] != 2 or j["upper"] != 3:
            raise AssertionError("joint uncertainty envelope or decision is wrong")
    if got["population_size_estimate"] is not None or got["all_channel_unobserved_count_estimate"] is not None:
        raise AssertionError("candidate promoted latent truth to an estimate")
    if any(oracle_summary[name]["all_channel_unobserved_truth_count"] != 1 for name in
           ("joint_boundary_linkage_independent_sources", "joint_boundary_linkage_shared_AB")):
        raise AssertionError("oracle common blind spot was not retained")
    return oracle_summary


def linkage_diagnostics(public, truth, got):
    truth_by_id = {x["scenario_id"]: x for x in truth["scenarios"]}
    diagnostics = {}
    for scenario in public["scenarios"]:
        oracle = truth_by_id[scenario["scenario_id"]]
        truth_map = oracle["record_to_event"]
        for run in next(x for x in got["scenarios"] if x["scenario_id"] == scenario["scenario_id"])["combinations"]:
            segmentation = scenario["segmentations"][run["segmentation_id"]]
            raw_by_node = {}
            for record_id, unit_id in segmentation.items():
                channel = next(r["channel"] for r in scenario["raw_records"] if r["record_id"] == record_id)
                raw_by_node.setdefault(f"{channel}:{unit_id}", []).append(record_id)
            groups = []
            for group in run["groups"]:
                event_ids = sorted({truth_map[rid] for node in group["nodes"] for rid in raw_by_node[node]})
                groups.append({"nodes": group["nodes"], "latent_event_ids": event_ids,
                               "mixed_latent_events": len(event_ids) > 1})
            event_to_groups = {}
            for index, group in enumerate(groups):
                for event_id in group["latent_event_ids"]:
                    event_to_groups.setdefault(event_id, []).append(index)
            diagnostics[f"{scenario['scenario_id']}:{run['combination_id']}"] = {
                "mixed_truth_components": sum(x["mixed_latent_events"] for x in groups),
                "fragmented_truth_events": sum(len(set(indices)) > 1 for indices in event_to_groups.values()),
                "groups": groups}
    clean = [v for k, v in diagnostics.items() if k.startswith("clean_unique_ids:")]
    if not clean or any(x["mixed_truth_components"] or x["fragmented_truth_events"] for x in clean):
        raise AssertionError("unique-ID oracle-linked control is not exact")
    return diagnostics


def mutation_controls(public, truth, got):
    cases = {}
    # Force consensus and remove all split units/assignments.
    p = copy.deepcopy(public); s = next(x for x in p["scenarios"] if x["scenario_id"] == "joint_boundary_linkage_shared_AB")
    truth_map = next(x for x in truth["scenarios"] if x["scenario_id"] == "joint_boundary_linkage_shared_AB")["record_to_event"]
    if truth_map["a_right"] != truth_map["b_right"] or truth_map["b_overlap"] == truth_map["c_overlap"]:
        raise AssertionError("missed/false linkage mutation truth preconditions failed")
    s["segmentations"].pop("split")
    for name in s["linkage_sets"].values(): name.pop("split")
    s["combinations"] = [x for x in s["combinations"] if x["segmentation"] == "merged"]
    s["analysis_sets"] = {"boundary_only": ["merged_hard"], "linkage_only": ["merged_hard", "merged_ambiguous"],
                           "joint": ["merged_hard", "merged_ambiguous"]}
    cases["forced_consensus_segmentation"] = (p, copy.deepcopy(got))

    p = copy.deepcopy(public); s = next(x for x in p["scenarios"] if x["scenario_id"] == "joint_boundary_linkage_shared_AB")
    s["linkage_sets"]["ambiguous"]["split"] = [e for e in s["linkage_sets"]["ambiguous"]["split"] if e["edge_id"] != "s_ab_right"]
    cases["delete_plausible_match"] = (p, copy.deepcopy(got))

    p = copy.deepcopy(public); s = next(x for x in p["scenarios"] if x["scenario_id"] == "joint_boundary_linkage_shared_AB")
    s["linkage_sets"]["ambiguous"]["split"].append({"edge_id": "false_overlap_link", "left": "B:b_overlap", "right": "C:c_overlap"})
    cases["add_false_match"] = (p, copy.deepcopy(got))

    g = copy.deepcopy(got); s = next(x for x in g["scenarios"] if x["scenario_id"] == "joint_boundary_linkage_shared_AB")
    row = next(x for x in s["combinations"] if x["combination_id"] == "split_ambiguous")
    row["multi_channel_overlap_count"] += 1
    cases["count_split_as_independent_failures"] = (copy.deepcopy(public), g)

    p = copy.deepcopy(public); s = next(x for x in p["scenarios"] if x["scenario_id"] == "joint_boundary_linkage_shared_AB")
    s["raw_records"] = [r for r in s["raw_records"] if r["record_id"] != "d_censored"]
    for mapping in s["segmentations"].values(): mapping.pop("d_censored")
    cases["drop_censored_opportunity"] = (p, copy.deepcopy(got))

    g = copy.deepcopy(got); s = next(x for x in g["scenarios"] if x["scenario_id"] == "joint_boundary_linkage_shared_AB")
    s["analysis_sets"]["joint"]["decision"] = "BELOW_THRESHOLD"
    g["all_channel_unobserved_count_estimate"] = 0
    cases["unidentified_to_zero_unseen"] = (copy.deepcopy(public), g)

    results = {}
    for name, (mutated_public, mutated_output) in cases.items():
        try:
            validate(mutated_public, truth, mutated_output)
            results[name] = "ESCAPED"
        except (AssertionError, KeyError, ValueError, TypeError):
            results[name] = "REJECTED"
    if any(value != "REJECTED" for value in results.values()):
        raise AssertionError(f"mutation escaped: {results}")
    return results


def main():
    frozen = json.loads((HERE / "FROZEN.json").read_text())
    for name, digest in frozen["source_sha256"].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != digest:
            raise AssertionError(f"frozen source hash mismatch: {name}")
    public = json.loads((HERE / "public_input.json").read_text())
    truth = json.loads((HERE / "auditor_truth.json").read_text())
    got = json.loads((HERE / "formal_output.json").read_text())
    summary = validate(public, truth, got)
    linkage = linkage_diagnostics(public, truth, got)
    mutations = mutation_controls(public, truth, got)
    result = {"pass": True, "method_disposition": "PASS_METHOD_SCOPED",
              "hypothesis_disposition": "H_PASS_SCOPED", "scenario_count": len(public["scenarios"]),
              "oracle_summary": summary, "linkage_diagnostics": linkage,
              "joint_interaction": {x["scenario_id"]: x["joint_interaction"] for x in got["scenarios"] if x["joint_interaction"]},
              "mutation_controls": mutations,
              "limitation": "The authored oracle fixture validates only finite unitization/linkage bookkeeping; no natural-trace model or safety inference."}
    (HERE / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
