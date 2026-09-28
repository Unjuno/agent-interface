"""One-generation Mindustry target acquisition and bounded cache routing.

The model returns two points from one image: Conveyor palette slot, then the
empty world tile directly above the copper source. This module grants no input
authority. The caller must revalidate the returned bundle before dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPOSITORY = next(parent for parent in HERE.parents if (parent / ".git").exists())
LIVE = REPOSITORY / "research" / "live_control"
sys.path.insert(0, str(LIVE))

from task_points_v1 import validate as validate_candidate  # noqa: E402


@dataclass(frozen=True)
class TargetBundle:
    palette_point: tuple[int, int]
    target_point: tuple[int, int]
    surface: int | str
    geometry: tuple[int, int, int, int]
    layout: str
    source_sequence: int


class RouteStop(RuntimeError):
    """Fail-closed route refusal before target input."""


def _binding(observation: dict) -> tuple[int | str, tuple[int, int, int, int]]:
    raw = observation.get("pointer_binding")
    if type(raw) is not dict:
        raise RouteStop("pointer binding unavailable")
    surface, geometry = raw.get("surface"), raw.get("geometry")
    if type(surface) not in (int, str) or type(geometry) is not list or len(geometry) != 4:
        raise RouteStop("exact surface geometry required")
    if any(type(value) is not int for value in geometry):
        raise RouteStop("integer surface geometry required")
    return surface, tuple(geometry)


def acquire_bundle(model_output: dict, observation: dict, width: int, height: int,
                   layout: str, palette_slots: list[dict]) -> TargetBundle:
    """Validate one model generation and bind its two ordered points to source."""
    if type(observation.get("sequence")) is not int or observation["sequence"] < 0:
        raise RouteStop("source observation sequence unavailable")
    surface, geometry = _binding(observation)
    try:
        candidate = validate_candidate(model_output, width, height)
    except ValueError as error:
        raise RouteStop("invalid model target output: " + str(error)) from error
    if candidate["status"] == "NEEDS_DECISION":
        raise RouteStop("model safely declined: " + candidate["reason"])
    if candidate["status"] != "DIRECT" or len(candidate["points"]) != 2:
        raise RouteStop("one generation must return palette and world points")
    palette, target = candidate["palette_point"], candidate["target_point"]
    if type(palette_slots) is not list or not palette_slots:
        raise RouteStop("fresh screen-derived palette slots required")
    try:
        slot_index = min(range(len(palette_slots)), key=lambda index:
            (palette_slots[index]["point"][0] - palette[0]) ** 2
            + (palette_slots[index]["point"][1] - palette[1]) ** 2)
        slot = palette_slots[slot_index]
        snapped_palette = slot["point"]
        distance_squared = ((snapped_palette[0] - palette[0]) ** 2
                            + (snapped_palette[1] - palette[1]) ** 2)
    except (KeyError, IndexError, TypeError) as error:
        raise RouteStop("invalid screen-derived palette slot set") from error
    if (type(snapped_palette) is not list or len(snapped_palette) != 2
            or any(type(value) is not int for value in snapped_palette)):
        raise RouteStop("integer screen-derived palette center required")
    if not (0 <= snapped_palette[0] < width and 0 <= snapped_palette[1] < height):
        raise RouteStop("screen-derived palette center outside source image")
    if distance_squared > 48 ** 2:
        raise RouteStop("coarse palette point outside 48px slot neighborhood")
    palette = snapped_palette
    if palette == target:
        raise RouteStop("palette and world target must be distinct")
    return TargetBundle(tuple(palette), tuple(target), surface, geometry,
                        layout, observation["sequence"])


def revalidate_bundle(bundle: TargetBundle, observation: dict,
                      layout: str) -> tuple[bool, str]:
    """Require a fresh observation and identical surface geometry before reuse."""
    surface, geometry = _binding(observation)
    sequence = observation.get("sequence")
    if type(sequence) is not int or sequence <= bundle.source_sequence:
        return False, "observation_not_newer_than_target"
    if layout != bundle.layout:
        return False, "layout_changed"
    if surface != bundle.surface or geometry != bundle.geometry:
        return False, "association_changed"
    return True, "revalidated"


def require_current_locator(bundle: TargetBundle, observation: dict,
                            layout: str) -> dict:
    """Final no-authority check required immediately before each target click."""
    eligible, reason = revalidate_bundle(bundle, observation, layout)
    if not eligible:
        raise RouteStop("target locator refused before input: " + reason)
    delivery_id = observation.get("delivery_id")
    if type(delivery_id) is not str or not delivery_id:
        raise RouteStop("flushed observation delivery identity required before input")
    return {"palette_point": list(bundle.palette_point),
            "target_point": list(bundle.target_point),
            "source_sequence": bundle.source_sequence,
            "validated_sequence": observation["sequence"],
            "delivery_id": delivery_id,
            "authority": "locator only; explicit caller action still required"}


def route_task(*, arm: str, route: str, task_id: str, layout: str,
               cached: TargetBundle | None, observation: dict, width: int,
               height: int, palette_slots: list[dict] | None, model_call) -> dict:
    """Resolve one frozen route and report any repair refusal before input.

    model_call(observation) returns one bounded-visual-target typed object. A
    returned bundle is only an observation-derived locator, never authority.
    """
    if arm not in {"plain", "ephemeral", "persistent"}:
        raise RouteStop("unknown arm")
    if arm != "persistent" and route != "cold":
        raise RouteStop("reference arms must use cold acquisition")
    if arm == "persistent" and task_id in {"A1", "B1"} and route not in {"cold", "repair"}:
        raise RouteStop("persistent acquisition schedule mismatch")
    if arm == "persistent" and task_id in {"A2", "A3", "B2", "B3"} and route != "reuse":
        raise RouteStop("persistent reuse schedule mismatch")

    if route == "cold":
        bundle = acquire_bundle(model_call(observation), observation, width, height,
                                layout, palette_slots)
        return {"bundle": bundle, "cache_update": bundle if arm == "persistent" else None,
                "model_calls": 1, "old_reference_pointer_admissions": 0,
                "old_reference_status": None}

    if cached is None:
        raise RouteStop("cached bundle required by route")
    eligible, reason = revalidate_bundle(cached, observation, layout)
    if route == "reuse":
        if not eligible:
            raise RouteStop("reuse refused before input: " + reason)
        return {"bundle": cached, "cache_update": cached, "model_calls": 0,
                "old_reference_pointer_admissions": 0,
                "old_reference_status": None}

    if route != "repair":
        raise RouteStop("unsupported route")
    if eligible:
        raise RouteStop("repair requires the prior target to be stale")
    # The old bundle is not returned to the caller and no pointer action occurs
    # before this single fresh model call.
    repaired = acquire_bundle(model_call(observation), observation, width, height,
                              layout, palette_slots)
    return {"bundle": repaired, "cache_update": repaired, "model_calls": 1,
            "old_reference_pointer_admissions": 0,
            "old_reference_status": "stale"}
