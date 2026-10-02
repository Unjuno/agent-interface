from __future__ import annotations

import argparse
import json
from pathlib import Path


TILE_WIDTH = 40
TILE_HEIGHT = 30
PATCH_RADIUS = 4
MIN_BLOCK_SITES = 8
SUPPORT = ((20, 15), (8, 8), (32, 8), (8, 22), (32, 22))
BLOCKS = ("northwest", "northeast", "southwest", "southeast")


def block_for(x: int, y: int) -> str | None:
    if x == 20 or y == 15:
        return None
    return ("north" if y < 15 else "south") + ("west" if x < 20 else "east")


def patch_disjoint(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1])) >= 2 * PATCH_RADIUS + 1


def enumerate_geometry() -> dict:
    # Strictly interior sites keep edge position out of this preflight's block contrast.
    sites = []
    for y in range(PATCH_RADIUS + 1, TILE_HEIGHT - PATCH_RADIUS - 1):
        for x in range(PATCH_RADIUS + 1, TILE_WIDTH - PATCH_RADIUS - 1):
            block = block_for(x, y)
            if block is None:
                continue
            distances = [max(abs(x - sx), abs(y - sy)) for sx, sy in SUPPORT]
            qualifies = all(d >= 2 * PATCH_RADIUS + 1 for d in distances)
            sites.append({"center": [x, y], "block": block,
                          "chebyshev_distance_to_support": distances,
                          "all_training_target_patches_disjoint": qualifies})
    qualifying = {block: [row["center"] for row in sites
                          if row["block"] == block and row["all_training_target_patches_disjoint"]]
                  for block in BLOCKS}
    counts = {block: len(qualifying[block]) for block in BLOCKS}
    decision = "GEOMETRY_FEASIBLE" if all(count >= MIN_BLOCK_SITES for count in counts.values()) else "HOLD_GEOMETRY_NOT_IDENTIFIABLE"
    return {"schema": "spatial-block-6590-t1-geometry-candidate-v1",
            "tile_width": TILE_WIDTH, "tile_height": TILE_HEIGHT,
            "patch_size": [2 * PATCH_RADIUS + 1, 2 * PATCH_RADIUS + 1],
            "support_centers": [list(p) for p in SUPPORT],
            "strict_interior_domain": {"x": [5, 34], "y": [5, 24]},
            "minimum_sites_per_block": MIN_BLOCK_SITES,
            "block_counts": counts, "qualifying_centers": qualifying,
            "enumerated_sites": sites, "decision": decision}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = enumerate_geometry()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "enumerated_sites"}, indent=2, sort_keys=True))
