"""Synthetic construction experiment for target-specific Mindustry receipts."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parent
REPOSITORY = next(parent for parent in ROOT.parents if (parent / ".git").exists())
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPOSITORY / "research" / "live_control"))

from receipt_target_admission_v1 import evaluate  # noqa: E402
from target_dispatch import compile_receipt_target_click  # noqa: E402
from target_receipts_v1 import (  # noqa: E402
    LOCATOR_AUTHORITY,
    ReceiptBuildStop,
    build_palette_receipt,
    build_world_receipt,
)


def observation(sequence: int, capture_ns: int) -> dict:
    return {"sequence": sequence, "capture_ns": capture_ns,
            "pointer_binding": {"focus": 10, "surface": 20,
                                "geometry": [0, 0, 128, 96]}}


def fixture():
    source = Image.new("RGB", (128, 96), "black")
    source.paste("red", (8, 8, 24, 24))       # palette target context
    source.paste("blue", (48, 32, 64, 48))    # model-frame world context
    selected = source.copy()
    selected.paste("yellow", (88, 8, 104, 24))  # selected-tool indicator
    selected.paste("green", (68, 32, 84, 48))   # world selection cue
    history = {
        1: {"observation": observation(1, 1_000_000), "image": source},
        2: {"observation": observation(2, 2_000_000), "image": selected},
    }
    locator = {"palette_point": [16, 16], "target_point": [56, 40],
               "source_sequence": 1, "validated_sequence": 3,
               "authority": LOCATOR_AUTHORITY}
    return source, selected, history, locator


class TargetReceiptConstructionTests(unittest.TestCase):
    def test_palette_receipt_revalidates_exact_model_frame_dependencies(self):
        source, _, history, locator = fixture()
        spec = build_palette_receipt(locator, exact_dependencies=[
            {"sequence": 1, "box": [8, 8, 24, 24]},
            {"sequence": 1, "box": [48, 32, 64, 48]},
        ])
        current = observation(4, 4_000_000)
        result = evaluate(spec, history, current, source.copy(), 4_100_000)
        self.assertTrue(result["eligible"], result)
        self.assertEqual(result["point"], [16, 16])
        self.assertEqual([check["kind"] for check in spec["checks"]],
                         ["exact_patch", "exact_patch"])

    def test_world_receipt_accepts_source_context_and_persisting_selection_cue(self):
        _, selected, history, locator = fixture()
        spec = build_world_receipt(locator,
            exact_dependencies=[
                {"sequence": 1, "box": [48, 32, 64, 48]},
                {"sequence": 2, "box": [88, 8, 104, 24]},
            ], selection_baseline_sequence=1,
            selection_receipt_sequence=2, selection_box=[68, 32, 84, 48],
            minimum_changed_pixels=16)
        result = evaluate(spec, history, observation(4, 4_000_000),
                          selected.copy(), 4_100_000)
        self.assertTrue(result["eligible"], result)
        self.assertEqual(result["point"], [56, 40])
        self.assertEqual([check["kind"] for check in spec["checks"]],
                         ["exact_patch", "exact_patch", "stable_change_mask"])

    def test_built_receipt_compiles_against_same_fresh_locator_boundary(self):
        _, _, _, locator = fixture()
        spec = build_palette_receipt(locator, exact_dependencies=[
            {"sequence": 1, "box": [8, 8, 24, 24]}])
        request = compile_receipt_target_click(
            locator, {"sequence": 3, "runtime_ns": 5_000_000}, "A1",
            "palette_point", spec)
        self.assertEqual(request["expected_sequence"], 3)
        self.assertEqual(request["steps"][0]["op"], "pointer_click_receipt_target")
        self.assertEqual(request["steps"][0]["receipt"], spec)

    def test_world_context_change_refuses_without_authority(self):
        _, selected, history, locator = fixture()
        spec = build_world_receipt(locator,
            exact_dependencies=[{"sequence": 1, "box": [48, 32, 64, 48]}],
            selection_baseline_sequence=1, selection_receipt_sequence=2,
            selection_box=[68, 32, 84, 48], minimum_changed_pixels=16)
        changed = selected.copy()
        changed.paste("white", (48, 32, 52, 36))
        result = evaluate(spec, history, observation(4, 4_000_000),
                          changed, 4_100_000)
        self.assertFalse(result["eligible"])
        self.assertEqual(result["authority_class"], "NO_TARGET_AUTHORITY")
        self.assertEqual(result["reason"], "exact_dependency_changed")
        self.assertIsNone(result["point"])

    def test_selection_mask_change_refuses_without_authority(self):
        _, selected, history, locator = fixture()
        spec = build_world_receipt(locator,
            exact_dependencies=[{"sequence": 1, "box": [48, 32, 64, 48]}],
            selection_baseline_sequence=1, selection_receipt_sequence=2,
            selection_box=[68, 32, 84, 48], minimum_changed_pixels=16)
        changed = selected.copy()
        changed.paste("black", (68, 32, 84, 48))
        result = evaluate(spec, history, observation(4, 4_000_000),
                          changed, 4_100_000)
        self.assertFalse(result["eligible"])
        self.assertEqual(result["authority_class"], "NO_TARGET_AUTHORITY")
        self.assertEqual(result["reason"], "stable_change_mask_changed")
        self.assertIsNone(result["point"])

    def test_builder_rejects_authority_and_temporal_mismatch(self):
        _, _, _, locator = fixture()
        bad_authority = {**locator, "authority": "TARGET_REFERENCE_ONLY"}
        with self.assertRaisesRegex(ReceiptBuildStop, "non-authorizing"):
            build_palette_receipt(bad_authority,
                exact_dependencies=[{"sequence": 1, "box": [8, 8, 24, 24]}])
        with self.assertRaisesRegex(ReceiptBuildStop, "decision boundary"):
            build_palette_receipt(locator,
                exact_dependencies=[{"sequence": 4, "box": [8, 8, 24, 24]}])
        with self.assertRaisesRegex(ReceiptBuildStop, "later pre-decision"):
            build_world_receipt(locator,
                exact_dependencies=[{"sequence": 1, "box": [48, 32, 64, 48]}],
                selection_baseline_sequence=1, selection_receipt_sequence=4,
                selection_box=[68, 32, 84, 48], minimum_changed_pixels=16)

    def test_world_builder_requires_model_frame_context_and_selection_mask(self):
        _, _, _, locator = fixture()
        with self.assertRaisesRegex(ReceiptBuildStop, "exact pixel dependencies"):
            build_world_receipt(locator, exact_dependencies=[],
                selection_baseline_sequence=1, selection_receipt_sequence=2,
                selection_box=[68, 32, 84, 48], minimum_changed_pixels=16)
        with self.assertRaisesRegex(ReceiptBuildStop, "positive changed-pixel"):
            build_world_receipt(locator,
                exact_dependencies=[{"sequence": 1, "box": [48, 32, 64, 48]}],
                selection_baseline_sequence=1, selection_receipt_sequence=2,
                selection_box=[68, 32, 84, 48], minimum_changed_pixels=True)

    def test_missing_historical_frame_stops_as_no_authority(self):
        _, selected, history, locator = fixture()
        spec = build_world_receipt(locator,
            exact_dependencies=[{"sequence": 1, "box": [48, 32, 64, 48]}],
            selection_baseline_sequence=1, selection_receipt_sequence=2,
            selection_box=[68, 32, 84, 48], minimum_changed_pixels=16)
        result = evaluate(spec, {2: history[2]}, observation(4, 4_000_000),
                          selected, 4_100_000)
        self.assertFalse(result["eligible"])
        self.assertEqual(result["authority_class"], "NO_TARGET_AUTHORITY")
        self.assertEqual(result["reason"], "historical_evidence_unavailable")
        self.assertIsNone(result["point"])


if __name__ == "__main__":
    unittest.main()
