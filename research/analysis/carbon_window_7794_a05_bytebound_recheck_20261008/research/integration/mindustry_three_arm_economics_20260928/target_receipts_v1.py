"""Construct bounded Mindustry receipts from a fresh, non-authoritative locator.

The builders describe pixel dependencies only. They do not establish semantic
identity or grant input authority; the receipt-aware runtime must revalidate
the dependencies against a newer observation immediately before dispatch.
"""

from __future__ import annotations

from pathlib import Path
import sys

LIVE = Path(__file__).resolve().parents[2] / "live_control"
sys.path.insert(0, str(LIVE))
from receipt_target_admission_v1 import validate as validate_receipt  # noqa: E402


LOCATOR_AUTHORITY = "locator only; explicit caller action still required"


class ReceiptBuildStop(ValueError):
    """Fail-closed refusal to construct an incomplete or unbound receipt."""


def _locator(locator: dict, target: str) -> tuple[list[int], int, int]:
    if type(locator) is not dict or locator.get("authority") != LOCATOR_AUTHORITY:
        raise ReceiptBuildStop("non-authorizing locator required")
    point = locator.get(target)
    if (type(point) is not list or len(point) != 2
            or any(type(value) is not int or value < 0 for value in point)):
        raise ReceiptBuildStop("screen-derived integer target point required")
    source = locator.get("source_sequence")
    decision = locator.get("validated_sequence")
    if (type(source) is not int or source < 1 or type(decision) is not int
            or decision < source):
        raise ReceiptBuildStop("ordered source and fresh decision sequences required")
    return point, source, decision


def _exact_checks(dependencies: list[dict], decision_sequence: int) -> list[dict]:
    if type(dependencies) is not list or not 1 <= len(dependencies) <= 7:
        raise ReceiptBuildStop("one to seven exact pixel dependencies required")
    checks = []
    for dependency in dependencies:
        if type(dependency) is not dict or set(dependency) != {"sequence", "box"}:
            raise ReceiptBuildStop("exact dependency needs only sequence and box")
        sequence, box = dependency["sequence"], dependency["box"]
        if (type(sequence) is not int or sequence < 1 or sequence > decision_sequence):
            raise ReceiptBuildStop("exact dependency must predate the decision boundary")
        if (type(box) is not list or len(box) != 4
                or any(type(value) is not int for value in box)):
            raise ReceiptBuildStop("integer half-open dependency box required")
        checks.append({"kind": "exact_patch", "source_sequence": sequence,
                       "box": list(box)})
    return checks


def _base(target: str, point: list[int], source: int, decision: int,
          ttl_ms: int, freshness_ms: int, checks: list[dict]) -> dict:
    spec = {"target": target,
            "point_space": "source_observation_pixels",
            "motion_model": "surface_origin_translation",
            "point": list(point), "source_sequence": source,
            "decision_after_sequence": decision, "ttl_ms": ttl_ms,
            "freshness_ms": freshness_ms, "checks": checks}
    try:
        validate_receipt(spec)
    except ValueError as error:
        raise ReceiptBuildStop("receipt admission contract rejected spec: " + str(error)) from error
    return spec


def build_palette_receipt(locator: dict, *, exact_dependencies: list[dict],
                          ttl_ms: int = 60_000,
                          freshness_ms: int = 1_000) -> dict:
    """Bind the palette point to exact source-frame UI/context patches."""
    point, source, decision = _locator(locator, "palette_point")
    checks = _exact_checks(exact_dependencies, decision)
    if any(item["source_sequence"] != source for item in checks):
        raise ReceiptBuildStop("palette dependencies must come from the model source frame")
    return _base("Mindustry Conveyor palette slot", point, source, decision,
                 ttl_ms, freshness_ms, checks)


def build_world_receipt(locator: dict, *, exact_dependencies: list[dict],
                        selection_baseline_sequence: int,
                        selection_receipt_sequence: int,
                        selection_box: list[int],
                        minimum_changed_pixels: int,
                        ttl_ms: int = 60_000,
                        freshness_ms: int = 1_000) -> dict:
    """Bind the world point to source context plus a stable selected-tool cue.

    Exact dependencies may include the original model-frame target context and
    a later, same-binding post-palette-selection indicator. The stable mask
    asserts that a visible selection change persists; it does not prove the
    selected icon's meaning, which remains outside this pixel receipt's scope.
    """
    point, source, decision = _locator(locator, "target_point")
    checks = _exact_checks(exact_dependencies, decision)
    baseline, receipt = selection_baseline_sequence, selection_receipt_sequence
    if (type(baseline) is not int or baseline != source
            or type(receipt) is not int or not source < receipt <= decision):
        raise ReceiptBuildStop("selection mask must bind source baseline to a later pre-decision frame")
    if (type(selection_box) is not list or len(selection_box) != 4
            or any(type(value) is not int for value in selection_box)):
        raise ReceiptBuildStop("integer selection-mask box required")
    if type(minimum_changed_pixels) is not int or minimum_changed_pixels < 1:
        raise ReceiptBuildStop("positive changed-pixel threshold required")
    checks.append({"kind": "stable_change_mask",
                   "baseline_sequence": baseline,
                   "receipt_sequence": receipt,
                   "box": list(selection_box),
                   "minimum_changed_pixels": minimum_changed_pixels})
    return _base("directly above Mindustry copper source", point, source,
                 decision, ttl_ms, freshness_ms, checks)
