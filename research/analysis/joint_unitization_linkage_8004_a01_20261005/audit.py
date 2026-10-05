"""Independent raw-fixture audit: no imports from candidate.py."""
from __future__ import annotations

import json
from pathlib import Path


def strict_overlap(left, right):
    return left[0] < right[1] and right[0] < left[1]


def audit(fixture, result):
    errors = []
    expected = {
        ("S0_boundary_left", "L0_false_candidate"): (False, False),
        ("S0_boundary_left", "L1_oracle_candidate"): (False, True),
        ("S1_boundary_right", "L0_false_candidate"): (True, False),
        ("S1_boundary_right", "L1_oracle_candidate"): (True, True),
    }
    if len(result.get("rows", [])) != len(expected):
        errors.append("assignment_denominator")
    actual = {}
    for row in result.get("rows", []):
        key = (row.get("segmentation"), row.get("linkage"))
        s = fixture["segmentations"].get(key[0])
        l = fixture["linkages"].get(key[1])
        if key in actual or key not in expected or s is None or l is None:
            errors.append("assignment_identity")
            continue
        temporal = strict_overlap(s["channel_a_unit_span"], fixture["truth"]["channel_b_raw_span"])
        identity = l["channel_a_link_key"] == fixture["truth"]["channel_b_identity"]
        if (temporal, identity) != expected[key]:
            errors.append("raw_assignment_reconstruction")
        linked = temporal and identity
        if row.get("temporal_overlap") != temporal or row.get("identity_match") != identity or row.get("linked") != linked:
            errors.append("candidate_row_reconstruction")
        if row.get("capture_history") != ("11" if linked else "10+01"):
            errors.append("capture_history")
        actual[key] = linked
    if set(actual) != set(expected):
        errors.append("missing_or_extra_assignment")
    baseline = actual.get(("S0_boundary_left", "L0_false_candidate"))
    s_only = actual.get(("S1_boundary_right", "L0_false_candidate"))
    l_only = actual.get(("S0_boundary_left", "L1_oracle_candidate"))
    joint = actual.get(("S1_boundary_right", "L1_oracle_candidate"))
    if not (baseline is False and s_only is False and l_only is False and joint is True):
        errors.append("factorial_interaction_gate")
    c = fixture["clean_control"]
    clean = strict_overlap(c["channel_a_span"], c["channel_b_span"]) and c["channel_a_link_key"] == c["channel_b_link_key"]
    if not clean or result.get("controls", {}).get("clean_control_linked") is not True:
        errors.append("clean_control")
    missing = fixture["missing_channel_control"]
    retained = missing["truth_present"] and missing["detected_by"] == []
    if not retained or result.get("controls", {}).get("oracle_all_channel_missing_opportunity_retained") is not True:
        errors.append("all_channel_missing_denominator")
    return {"ok": not errors, "errors": errors, "assignments_reconstructed": len(actual), "scope": "authored finite existence fixture only"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="fixture.json")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    f = json.loads(Path(args.fixture).read_text())
    c = json.loads(Path(args.candidate).read_text())
    result = audit(f, c)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
