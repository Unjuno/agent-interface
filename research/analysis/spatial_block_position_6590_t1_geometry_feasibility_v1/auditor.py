from __future__ import annotations

import argparse
import json
from pathlib import Path


WIDTH, HEIGHT, RADIUS, MINIMUM = 40, 30, 4, 8
TRAINING_SITES = ((20, 15), (8, 8), (32, 8), (8, 22), (32, 22))
QUADRANTS = ("northwest", "northeast", "southwest", "southeast")


def independent_rows():
    rows = []
    # Reconstruct independently from explicit tile and split definitions.
    for row in range(5, 25):
        for column in range(5, 35):
            if column == 20 or row == 15:
                continue
            if row < 15:
                quadrant = "northwest" if column < 20 else "northeast"
            else:
                quadrant = "southwest" if column < 20 else "southeast"
            gaps = tuple(max(abs(column - sx), abs(row - sy)) for sx, sy in TRAINING_SITES)
            is_disjoint = all(gap >= 9 for gap in gaps)
            rows.append({"center": [column, row], "block": quadrant,
                         "chebyshev_distance_to_support": list(gaps),
                         "all_training_target_patches_disjoint": is_disjoint})
    return rows


def audit_payload(candidate: dict) -> dict:
    expected = independent_rows()
    by_block = {name: [r["center"] for r in expected
                       if r["block"] == name and r["all_training_target_patches_disjoint"]]
                for name in QUADRANTS}
    counts = {name: len(by_block[name]) for name in QUADRANTS}
    errors = []
    fixed_metadata = {"schema": "spatial-block-6590-t1-geometry-candidate-v1",
                      "tile_width": 40, "tile_height": 30, "patch_size": [9, 9],
                      "support_centers": [list(site) for site in TRAINING_SITES],
                      "strict_interior_domain": {"x": [5, 34], "y": [5, 24]}}
    for key, value in fixed_metadata.items():
        if candidate.get(key) != value:
            errors.append(f"frozen_geometry_metadata_mismatch:{key}")
    if candidate.get("enumerated_sites") != expected:
        errors.append("raw_site_reconstruction_mismatch")
    if candidate.get("qualifying_centers") != by_block or candidate.get("block_counts") != counts:
        errors.append("qualifying_site_aggregation_mismatch")
    if candidate.get("minimum_sites_per_block") != MINIMUM:
        errors.append("minimum_support_binding_mismatch")
    expected_decision = "GEOMETRY_FEASIBLE" if all(n >= MINIMUM for n in counts.values()) else "HOLD_GEOMETRY_NOT_IDENTIFIABLE"
    if candidate.get("decision") != expected_decision:
        errors.append("decision_mismatch")
    return {"schema": "spatial-block-6590-t1-geometry-audit-v1",
            "decision": "PASS_GEOMETRY_AUDIT" if not errors else "HOLD_AUDIT_INTEGRITY",
            "errors": errors, "independently_reconstructed_sites": len(expected),
            "block_counts": counts, "minimum_sites_per_block": MINIMUM,
            "geometry_decision": expected_decision,
            "candidate_bytes_reconstructed": not errors}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    candidate = json.loads(args.raw.read_text(encoding="utf-8"))
    result = audit_payload(candidate)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 2)
