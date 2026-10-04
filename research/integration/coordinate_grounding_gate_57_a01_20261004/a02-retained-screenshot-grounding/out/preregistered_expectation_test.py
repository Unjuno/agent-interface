from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parents[3]))

from runtime.guarded_x11_v1.handles import TargetHandleStore
from runtime.guarded_x11_v1.handles_texture import FlatTargetRefused


CASES = json.loads((HERE / "INPUTS.json").read_text(encoding="utf-8"))["tasks"]
NOW_NS = 2_000_000
REGION = 24


def observe(sequence: int, capture_ns: int, size: tuple[int, int]) -> dict:
    return {
        "sequence": sequence,
        "capture_ns": capture_ns,
        "pointer_binding": {
            "focus": 101,
            "surface": 202,
            "geometry": [0, 0, size[0], size[1]],
        },
    }


def check_point(case: dict, point: list[int]) -> dict:
    with Image.open(HERE / case["image_file"]) as source:
        image = source.convert("RGB")
    width, height = image.size
    store = TargetHandleStore("a02-retained-screen-grounding", id_factory=lambda: "private")
    box = [point[0] - REGION // 2, point[1] - REGION // 2, REGION, REGION]
    try:
        minted = store.mint(
            "proposed_coordinate", "window_content", box,
            observe(1, 1_000_000, image.size), image, NOW_NS,
            ttl_ms=300_000, freshness_ms=1_500, search_radius=0,
            allowed_transformations=("window_translation",),
        )
    except FlatTargetRefused:
        return {"status": "FLAT_REFUSED", "eligible": False, "registry_entries": len(store._entries)}
    resolved = store.resolve_point(
        minted["handle"], [REGION // 2, REGION // 2],
        observe(2, NOW_NS, image.size), image.copy(), NOW_NS + 1_000_000,
    )
    return {
        "status": resolved["status"],
        "eligible": resolved["eligible"],
        "reason": resolved.get("reason"),
        "registry_entries": len(store._entries),
    }


class RetainedScreenshotGroundingTests(unittest.TestCase):
    def test_visible_form_coordinates_resolve(self):
        rows = [case for case in CASES if case["task"] != 3]
        outcomes = [
            (case["task"], role, check_point(case, case[f"{role}_point"]))
            for case in rows for role in ("field", "submit")
        ]
        self.assertEqual(len(outcomes), 8)
        self.assertTrue(all(result["status"] == "VALID" and result["eligible"] is True
                            for _, _, result in outcomes), outcomes)

    def test_blank_page_coordinates_refuse_before_registry_insert(self):
        case = next(case for case in CASES if case["task"] == 3)
        outcomes = [check_point(case, case[role]) for role in ("field_point", "submit_point")]
        self.assertEqual(outcomes, [
            {"status": "FLAT_REFUSED", "eligible": False, "registry_entries": 0},
            {"status": "FLAT_REFUSED", "eligible": False, "registry_entries": 0},
        ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
