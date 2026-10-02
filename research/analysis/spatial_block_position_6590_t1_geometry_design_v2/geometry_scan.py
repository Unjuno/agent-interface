"""Preformal deterministic geometry scan for an additive #6590 T1 redesign.

This is a design-screening tool only. It does not generate images or fit a model.
"""
from __future__ import annotations

import json
from typing import Any


PATCH_RADIUS = 4
MIN_CHEBYSHEV_GAP = 9
MIN_CENTERS_PER_BLOCK = 8
DISTRACTOR_CENTER = (4, 4)
TILE_CANDIDATES = ((80, 60), (96, 72), (112, 84), (128, 96))


def geometry(width: int, height: int) -> dict[str, Any]:
    cx, cy = width // 2, height // 2
    dx, dy = max(9, width // 12), max(9, height // 8)
    support = ((cx, cy), (cx - dx, cy - dy), (cx + dx, cy - dy),
               (cx - dx, cy + dy), (cx + dx, cy + dy))

    # Grid pitch equals patch width: candidate target patches cannot overlap.
    grid_x = range(9, width - 9, MIN_CHEBYSHEV_GAP)
    grid_y = range(9, height - 9, MIN_CHEBYSHEV_GAP)
    blocks: dict[str, list[list[int]]] = {k: [] for k in ("northwest", "northeast", "southwest", "southeast")}
    rejected_support = rejected_distractor = 0
    for y in grid_y:
        for x in grid_x:
            if any(max(abs(x - sx), abs(y - sy)) < MIN_CHEBYSHEV_GAP for sx, sy in support):
                rejected_support += 1
                continue
            if max(abs(x - DISTRACTOR_CENTER[0]), abs(y - DISTRACTOR_CENTER[1])) < MIN_CHEBYSHEV_GAP:
                rejected_distractor += 1
                continue
            side = ("north" if y < cy else "south") + ("west" if x < cx else "east")
            blocks[side].append([x, y])

    counts = {name: len(sites) for name, sites in blocks.items()}
    feasible = all(n >= MIN_CENTERS_PER_BLOCK for n in counts.values())
    return {
        "tile": [width, height],
        "patch": [9, 9],
        "training_support_centers": [list(p) for p in support],
        "negative_distractor_center": list(DISTRACTOR_CENTER),
        "candidate_grid_origin": [9, 9],
        "candidate_grid_pitch": MIN_CHEBYSHEV_GAP,
        "eligible_centers_by_block": blocks,
        "eligible_counts": counts,
        "rejected_for_support_proximity": rejected_support,
        "rejected_for_distractor_proximity": rejected_distractor,
        "minimum_centers_per_block": MIN_CENTERS_PER_BLOCK,
        "decision": "GEOMETRY_FEASIBLE_CANDIDATE" if feasible else "HOLD_GEOMETRY_NOT_IDENTIFIABLE",
    }


def scan() -> dict[str, Any]:
    return {
        "status": "PREFORMAL_GEOMETRY_SCREEN_ONLY",
        "no_images_generated": True,
        "model_fits": 0,
        "tile_candidates": [geometry(*tile) for tile in TILE_CANDIDATES],
    }


if __name__ == "__main__":
    print(json.dumps(scan(), indent=2, sort_keys=True))
