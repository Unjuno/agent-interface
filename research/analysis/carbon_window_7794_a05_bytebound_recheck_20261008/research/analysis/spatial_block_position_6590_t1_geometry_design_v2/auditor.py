"""Independent raw-only reconstruction for the preformal geometry screen."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# Independently restated from the prospective layout question; deliberately
# not imported from the candidate implementation.
_TILES = ((80, 60), (96, 72), (112, 84), (128, 96))
_PATCH_RADIUS = 4
_GAP = 9
_MIN_BLOCK_SITES = 8
_DISTRACTOR = (4, 4)


def audit(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if payload.get("status") != "PREFORMAL_GEOMETRY_SCREEN_ONLY":
        errors.append("wrong_screen_status")
    if payload.get("no_images_generated") is not True or payload.get("model_fits") != 0:
        errors.append("scope_claim_mismatch")
    actual_designs = payload.get("tile_candidates")
    if not isinstance(actual_designs, list) or len(actual_designs) != len(_TILES):
        return {"decision": "HOLD_AUDIT_INTEGRITY", "errors": errors + ["tile_candidate_coverage_mismatch"]}

    for index, ((width, height), row) in enumerate(zip(_TILES, actual_designs)):
        # Reconstruct support coordinates from geometry parameters rather than
        # trusting the candidate's center lists or its eligible-site table.
        mid_x, mid_y = width // 2, height // 2
        off_x, off_y = max(9, width // 12), max(9, height // 8)
        support = ((mid_x, mid_y), (mid_x - off_x, mid_y - off_y),
                   (mid_x + off_x, mid_y - off_y), (mid_x - off_x, mid_y + off_y),
                   (mid_x + off_x, mid_y + off_y))
        expected: dict[str, list[list[int]]] = {
            "northwest": [], "northeast": [], "southwest": [], "southeast": []}
        rejected_support = rejected_distractor = 0
        for x in range(9, width - 9, _GAP):
            for y in range(9, height - 9, _GAP):
                overlap = False
                for sx, sy in support:
                    if abs(x - sx) < _GAP and abs(y - sy) < _GAP:
                        overlap = True
                        break
                if overlap:
                    rejected_support += 1
                    continue
                if abs(x - _DISTRACTOR[0]) < _GAP and abs(y - _DISTRACTOR[1]) < _GAP:
                    rejected_distractor += 1
                    continue
                if x - _PATCH_RADIUS < 5 or width - (x + _PATCH_RADIUS + 1) < 5:
                    errors.append(f"design_{index}:insufficient_horizontal_edge_margin")
                if y - _PATCH_RADIUS < 5 or height - (y + _PATCH_RADIUS + 1) < 5:
                    errors.append(f"design_{index}:insufficient_vertical_edge_margin")
                quadrant = ("north" if y < mid_y else "south") + ("west" if x < mid_x else "east")
                expected[quadrant].append([x, y])

        for sites in expected.values():
            sites.sort(key=lambda point: (point[1], point[0]))
        reported = row.get("eligible_centers_by_block")
        if reported != expected:
            errors.append(f"design_{index}:eligible_sites_mismatch")
        actual_counts = row.get("eligible_counts")
        exact_counts = {name: len(sites) for name, sites in expected.items()}
        if actual_counts != exact_counts:
            errors.append(f"design_{index}:count_mismatch")
        if (row.get("tile") != [width, height]
                or row.get("patch") != [9, 9]
                or row.get("training_support_centers") != [list(p) for p in support]
                or row.get("negative_distractor_center") != list(_DISTRACTOR)
                or row.get("candidate_grid_origin") != [9, 9]
                or row.get("candidate_grid_pitch") != _GAP
                or row.get("minimum_centers_per_block") != _MIN_BLOCK_SITES):
            errors.append(f"design_{index}:geometry_metadata_mismatch")
        if row.get("rejected_for_support_proximity") != rejected_support:
            errors.append(f"design_{index}:support_rejection_count_mismatch")
        if row.get("rejected_for_distractor_proximity") != rejected_distractor:
            errors.append(f"design_{index}:distractor_rejection_count_mismatch")
        should_be_feasible = all(value >= _MIN_BLOCK_SITES for value in exact_counts.values())
        expected_decision = "GEOMETRY_FEASIBLE_CANDIDATE" if should_be_feasible else "HOLD_GEOMETRY_NOT_IDENTIFIABLE"
        if row.get("decision") != expected_decision:
            errors.append(f"design_{index}:decision_mismatch")

    return {
        "decision": "PASS_GEOMETRY_SCREEN_AUDIT" if not errors else "HOLD_AUDIT_INTEGRITY",
        "audited_tile_candidates": len(actual_designs),
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.input.read_text(encoding="utf-8")))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
