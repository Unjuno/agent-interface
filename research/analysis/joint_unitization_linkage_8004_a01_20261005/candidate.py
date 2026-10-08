"""Tiny exhaustive candidate for Issue #8004's joint-ambiguity existence fixture."""
from __future__ import annotations

import itertools
import json
from pathlib import Path


def overlaps(a: list[int], b: list[int]) -> bool:
    return max(a[0], b[0]) < min(a[1], b[1])


def evaluate(fixture: dict) -> dict:
    rows = []
    for (s_name, segmentation), (l_name, linkage) in itertools.product(
        fixture["segmentations"].items(), fixture["linkages"].items()
    ):
        temporal = overlaps(segmentation["channel_a_unit_span"], fixture["truth"]["channel_b_raw_span"])
        identity = linkage["channel_a_link_key"] == fixture["truth"]["channel_b_identity"]
        linked = temporal and identity
        rows.append({
            "segmentation": s_name,
            "linkage": l_name,
            "temporal_overlap": temporal,
            "identity_match": identity,
            "linked": linked,
            "capture_history": "11" if linked else "10+01",
        })
    baseline = rows[0]["linked"]
    segmentation_only = next(row["linked"] for row in rows if row["segmentation"] != rows[0]["segmentation"] and row["linkage"] == rows[0]["linkage"])
    linkage_only = next(row["linked"] for row in rows if row["segmentation"] == rows[0]["segmentation"] and row["linkage"] != rows[0]["linkage"])
    joint = next(row["linked"] for row in rows if row["segmentation"] != rows[0]["segmentation"] and row["linkage"] != rows[0]["linkage"])
    mixed = {baseline, segmentation_only, linkage_only, joint}
    control = fixture["clean_control"]
    control_linked = (
        overlaps(control["channel_a_span"], control["channel_b_span"])
        and control["channel_a_link_key"] == control["channel_b_link_key"]
    )
    return {
        "rows": rows,
        "factorial": {
            "baseline_linked": baseline,
            "segmentation_only_linked": segmentation_only,
            "linkage_only_linked": linkage_only,
            "joint_linked": joint,
            "one_factor_ranges_stable": len({baseline, segmentation_only}) == 1 and len({baseline, linkage_only}) == 1,
            "joint_changes_decision": joint != baseline,
            "disposition": "UNIDENTIFIED" if len(mixed) > 1 else "STABLE",
        },
        "controls": {
            "clean_control_linked": control_linked,
            "oracle_all_channel_missing_opportunity_retained": fixture["missing_channel_control"]["truth_present"] and not fixture["missing_channel_control"]["detected_by"],
        },
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="fixture.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = evaluate(json.loads(Path(args.fixture).read_text()))
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["factorial"], sort_keys=True))
