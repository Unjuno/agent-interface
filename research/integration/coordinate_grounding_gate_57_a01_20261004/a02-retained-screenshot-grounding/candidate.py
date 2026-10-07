from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageStat

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from runtime.guarded_x11_v1.handles import TargetHandleStore
from runtime.guarded_x11_v1.handles_texture import FlatTargetRefused

NOW_NS = 2_000_000
REGION = 24


def observation(sequence: int, capture_ns: int, image_size: tuple[int, int]) -> dict:
    return {
        "sequence": sequence,
        "capture_ns": capture_ns,
        "pointer_binding": {
            "focus": 101,
            "surface": 202,
            "geometry": [0, 0, image_size[0], image_size[1]],
        },
    }


def evaluate_coordinate(case: dict, role: str) -> dict:
    point = case[f"{role}_point"]
    with Image.open(HERE / case["image_file"]) as image_file:
        image = image_file.convert("RGB")
    x, y = point
    box = [x - REGION // 2, y - REGION // 2, REGION, REGION]
    max_patch_stddev = max(ImageStat.Stat(image.crop((x - 12, y - 12, x + 12, y + 12))).stddev)
    store = TargetHandleStore("a02-retained-screen-grounding", id_factory=lambda: "private")
    try:
        handle = store.mint(
            "proposed_coordinate", "window_content", box,
            observation(1, 1_000_000, image.size), image, NOW_NS,
            ttl_ms=300_000, freshness_ms=1_500, search_radius=0,
            allowed_transformations=("window_translation",),
        )
    except FlatTargetRefused as exc:
        return {
            "task": case["task"], "role": role, "point": point,
            "status": "FLAT_REFUSED", "eligible": False,
            "max_patch_stddev": round(max_patch_stddev, 6),
            "reason": str(exc), "registry_entries": len(store._entries),
        }
    result = store.resolve_point(
        handle["handle"], [REGION // 2, REGION // 2],
        observation(2, NOW_NS, image.size), image.copy(), NOW_NS + 1_000_000,
    )
    return {
        "task": case["task"], "role": role, "point": point,
        "status": result["status"], "eligible": result["eligible"],
        "max_patch_stddev": round(max_patch_stddev, 6),
        "reason": result.get("reason"), "registry_entries": len(store._entries),
    }


def run_experiment() -> dict:
    manifest = json.loads((HERE / "INPUTS.json").read_text(encoding="utf-8"))
    rows = [
        evaluate_coordinate(case, role)
        for case in manifest["tasks"]
        for role in ("field", "submit")
    ]
    return {
        "schema": "a02-retained-screenshot-grounding-result-v1",
        "input_source_pr_head": manifest["source_pr_head"],
        "source_runtime_main_snapshot": manifest["source_main_snapshot"],
        "target_region_px": REGION,
        "cases": rows,
        "summary": {
            "coordinate_count": len(rows),
            "valid": sum(row["status"] == "VALID" for row in rows),
            "flat_refused": sum(row["status"] == "FLAT_REFUSED" for row in rows),
            "other_status": sum(row["status"] not in {"VALID", "FLAT_REFUSED"} for row in rows),
            "input_dispatch_count": 0,
            "model_call_count": 0,
            "gui_call_count": 0,
        },
        "interpretation": "descriptive offline replay only; local texture-match admission is not semantic target verification",
    }


if __name__ == "__main__":
    print(json.dumps(run_experiment(), indent=2, sort_keys=True))
