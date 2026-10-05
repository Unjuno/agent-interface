#!/usr/bin/env python3
"""Write the frozen public trace fixture and separate auditor-only latent truth."""
import json
import copy
from pathlib import Path

HERE = Path(__file__).parent


def edge(edge_id, left, right):
    return {"edge_id": edge_id, "left": left, "right": right}


def record(record_id, channel, start, end, censored=False, trace="trace-main"):
    return {"record_id": record_id, "channel": channel, "start": start, "end": end,
            "right_censored": censored, "trace_id": trace}


def main():
    clean_records = [record("ca", "A", 1, 2), record("cb", "B", 1, 2), record("cc", "C", 1, 2),
                     record("da", "A", 5, 6), record("db", "B", 5, 6),
                     record("ea", "A", 9, 10), record("ec", "C", 9, 10), record("fb", "B", 14, 15)]
    clean_map = {x["record_id"]: x["record_id"] for x in clean_records}
    clean_edges = [edge("clean-e1-ab", "A:ca", "B:cb"), edge("clean-e1-ac", "A:ca", "C:cc"),
                   edge("clean-e2-ab", "A:da", "B:db"), edge("clean-e3-ac", "A:ea", "C:ec")]
    clean = {"scenario_id": "clean_unique_ids", "channels": ["A", "B", "C", "D"],
             "raw_records": clean_records, "missing_intervals": [], "segmentations": {"exact": clean_map},
             "source_dependence_groups": {"A": "independent-A", "B": "independent-B", "C": "independent-C", "D": "independent-D"},
             "linkage_sets": {"exact": {"exact": clean_edges}},
             "combinations": [{"id": "exact", "segmentation": "exact", "linkage": "exact"}],
             "analysis_sets": {"clean": ["exact"]}, "decision_threshold_multi_channel": 3}

    records = [
        record("a_left", "A", 10, 12), record("a_right", "A", 20, 22), record("a_stable", "A", 30, 32),
        record("a_gap", "A", 50, 52), record("b_left", "B", 10, 12), record("b_right", "B", 20, 22),
        record("b_only", "B", 34, 35), record("b_overlap", "B", 40, 45), record("c_left", "C", 10, 12),
        record("c_stable", "C", 30, 32), record("c_only", "C", 36, 37), record("c_overlap", "C", 42, 47),
        record("d_only", "D", 38, 39), record("d_censored", "D", 58, 60, censored=True),
    ]
    merged = {x["record_id"]: x["record_id"] for x in records}
    merged["a_left"] = merged["a_right"] = "a_pair"
    split = {x["record_id"]: x["record_id"] for x in records}
    hard_merged = [edge("m_ab_left", "A:a_pair", "B:b_left"), edge("m_ac_left", "A:a_pair", "C:c_left"),
                   edge("stable_ac", "A:a_stable", "C:c_stable")]
    all_merged = [edge("m_ab_right", "A:a_pair", "B:b_right"), edge("m_ac_left", "A:a_pair", "C:c_left"),
                  edge("stable_ac", "A:a_stable", "C:c_stable")]
    hard_split = [edge("s_ab_left", "A:a_left", "B:b_left"), edge("s_ac_left", "A:a_left", "C:c_left"),
                  edge("stable_ac", "A:a_stable", "C:c_stable")]
    all_split = hard_split + [edge("s_ab_right", "A:a_right", "B:b_right")]
    main = {"scenario_id": "joint_boundary_linkage", "channels": ["A", "B", "C", "D"],
            "raw_records": records, "missing_intervals": [{"channel": "D", "start": 48, "end": 53, "reason": "telemetry_gap"}],
            "source_dependence_groups": {"A": "shared-pipeline-1", "B": "shared-pipeline-1", "C": "independent-C", "D": "independent-D"},
            "segmentations": {"merged": merged, "split": split},
            "linkage_sets": {"hard": {"merged": hard_merged, "split": hard_split},
                             "ambiguous": {"merged": all_merged, "split": all_split}},
            "combinations": [
                {"id": "merged_hard", "segmentation": "merged", "linkage": "hard"},
                {"id": "split_hard", "segmentation": "split", "linkage": "hard"},
                {"id": "merged_ambiguous", "segmentation": "merged", "linkage": "ambiguous"},
                {"id": "split_ambiguous", "segmentation": "split", "linkage": "ambiguous"}],
            "analysis_sets": {"boundary_only": ["merged_hard", "split_hard"],
                              "linkage_only": ["merged_hard", "merged_ambiguous"],
                              "joint": ["merged_hard", "split_hard", "merged_ambiguous", "split_ambiguous"]},
            "decision_threshold_multi_channel": 3}
    independent = copy.deepcopy(main)
    independent["scenario_id"] = "joint_boundary_linkage_independent_sources"
    independent["source_dependence_groups"] = {"A": "independent-A", "B": "independent-B", "C": "independent-C", "D": "independent-D"}
    shared = copy.deepcopy(main)
    shared["scenario_id"] = "joint_boundary_linkage_shared_AB"
    public = {"protocol": "issue-8004-t0-a02-v1", "scenarios": [clean, independent, shared]}

    clean_truth = {"scenario_id": "clean_unique_ids", "record_to_event": {"ca": "e1", "cb": "e1", "cc": "e1",
        "da": "e2", "db": "e2", "ea": "e3", "ec": "e3", "fb": "e4"},
        "latent_events": [
            {"event_id": "e1", "channel_status": {"A": "CAPTURED", "B": "CAPTURED", "C": "CAPTURED", "D": "OBSERVED_ZERO"}},
            {"event_id": "e2", "channel_status": {"A": "CAPTURED", "B": "CAPTURED", "C": "OBSERVED_ZERO", "D": "OBSERVED_ZERO"}},
            {"event_id": "e3", "channel_status": {"A": "CAPTURED", "B": "OBSERVED_ZERO", "C": "CAPTURED", "D": "OBSERVED_ZERO"}},
            {"event_id": "e4", "channel_status": {"A": "OBSERVED_ZERO", "B": "CAPTURED", "C": "OBSERVED_ZERO", "D": "OBSERVED_ZERO"}}]}
    main_truth = {"scenario_id": "joint_boundary_linkage", "record_to_event": {
        "a_left": "e1", "b_left": "e1", "c_left": "e1", "a_right": "e2", "b_right": "e2",
        "a_stable": "e3", "c_stable": "e3", "b_only": "e4", "c_only": "e5", "d_only": "e6",
        "b_overlap": "e7b", "c_overlap": "e7c", "a_gap": "e8", "d_censored": "e9"},
        "latent_events": [
            {"event_id": "e1", "channel_status": {"A": "CAPTURED", "B": "CAPTURED", "C": "CAPTURED", "D": "OBSERVED_ZERO"}},
            {"event_id": "e2", "channel_status": {"A": "CAPTURED", "B": "CAPTURED", "C": "OBSERVED_ZERO", "D": "OBSERVED_ZERO"}},
            {"event_id": "e3", "channel_status": {"A": "CAPTURED", "B": "OBSERVED_ZERO", "C": "CAPTURED", "D": "OBSERVED_ZERO"}},
            {"event_id": "e4", "channel_status": {"A": "OBSERVED_ZERO", "B": "CAPTURED", "C": "OBSERVED_ZERO", "D": "OBSERVED_ZERO"}},
            {"event_id": "e5", "channel_status": {"A": "OBSERVED_ZERO", "B": "OBSERVED_ZERO", "C": "CAPTURED", "D": "OBSERVED_ZERO"}},
            {"event_id": "e6", "channel_status": {"A": "OBSERVED_ZERO", "B": "OBSERVED_ZERO", "C": "OBSERVED_ZERO", "D": "CAPTURED"}},
            {"event_id": "e7b", "channel_status": {"A": "OBSERVED_ZERO", "B": "CAPTURED", "C": "OBSERVED_ZERO", "D": "OBSERVED_ZERO"}},
            {"event_id": "e7c", "channel_status": {"A": "OBSERVED_ZERO", "B": "OBSERVED_ZERO", "C": "CAPTURED", "D": "OBSERVED_ZERO"}},
            {"event_id": "e8", "channel_status": {"A": "CAPTURED", "B": "OBSERVED_ZERO", "C": "OBSERVED_ZERO", "D": "MISSING"}},
            {"event_id": "e9", "channel_status": {"A": "OBSERVED_ZERO", "B": "OBSERVED_ZERO", "C": "OBSERVED_ZERO", "D": "RIGHT_CENSORED_CAPTURED"}},
            {"event_id": "e10", "channel_status": {"A": "OBSERVED_ZERO", "B": "OBSERVED_ZERO", "C": "OBSERVED_ZERO", "D": "OBSERVED_ZERO"}}]}
    independent_truth = copy.deepcopy(main_truth)
    independent_truth["scenario_id"] = "joint_boundary_linkage_independent_sources"
    shared_truth = copy.deepcopy(main_truth)
    shared_truth["scenario_id"] = "joint_boundary_linkage_shared_AB"
    truth = {"protocol": "issue-8004-t0-a02-oracle-v1", "scenarios": [clean_truth, independent_truth, shared_truth]}
    (HERE / "public_input.json").write_text(json.dumps(public, sort_keys=True, indent=2) + "\n")
    (HERE / "auditor_truth.json").write_text(json.dumps(truth, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
