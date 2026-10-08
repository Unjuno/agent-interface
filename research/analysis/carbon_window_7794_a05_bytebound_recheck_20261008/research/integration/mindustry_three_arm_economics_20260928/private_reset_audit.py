"""Independent host checks for the benchmark-private Mindustry reset witness."""

from __future__ import annotations

import math


TARGET = (137, 52)
GUARD = {(x, y) for y in range(48, 56) for x in range(136, 150)}
SNAPSHOT_KEYS = {"tick", "paused", "tiles", "copper", "core_x", "core_y",
                 "source_item", "player_dead", "unit"}
TILE_KEYS = {"x", "y", "block", "team", "rotation", "floor", "overlay"}
EXPECTED_SCORE_SCOPE = (
    "one changed-geometry Mindustry placement; no delivery or route-completion claim")


def _tile_map(snapshot: dict) -> dict[tuple[int, int], dict]:
    rows = snapshot.get("tiles")
    if type(rows) is not list or len(rows) != len(GUARD):
        raise ValueError("complete 112-tile guard projection required")
    result = {}
    for row in rows:
        if type(row) is not dict or set(row) != TILE_KEYS:
            raise ValueError("exact engine tile projection required")
        if type(row["x"]) is not int or type(row["y"]) is not int:
            raise ValueError("integer tile coordinates required")
        coordinate = (row["x"], row["y"])
        if coordinate not in GUARD or coordinate in result:
            raise ValueError("duplicate or out-of-guard tile")
        if not all(type(row[field]) is str and row[field]
                   for field in ("block", "floor", "overlay")):
            raise ValueError("invalid tile block/floor/overlay")
        if type(row["team"]) is not int:
            raise ValueError("invalid tile team")
        if row["rotation"] is not None and (type(row["rotation"]) is not int
                                               or not 0 <= row["rotation"] <= 3):
            raise ValueError("invalid tile rotation")
        result[coordinate] = row
    if set(result) != GUARD:
        raise ValueError("guard coordinate coverage mismatch")
    return result


def verify_reset_witness(before: dict, reset: dict) -> dict:
    """Check that private reset restored the exact pre-task game projection."""
    errors = []
    try:
        if type(before) is not dict or set(before) != SNAPSHOT_KEYS:
            raise ValueError("exact pre-task snapshot required")
        if type(reset) is not dict or set(reset) != SNAPSHOT_KEYS:
            raise ValueError("exact reset snapshot required")
        original_tiles, reset_tiles = _tile_map(before), _tile_map(reset)
        if before["paused"] is not True or reset["paused"] is not True:
            errors.append("paused_state_not_restored")
        if before["player_dead"] is not False or reset["player_dead"] is not False:
            errors.append("live_player_not_restored")
        if (type(reset["unit"]) is not dict
                or set(reset["unit"]) != {"x", "y", "type", "plans"}
                or type(reset["unit"].get("plans")) is not int
                or reset["unit"]["plans"] != 0
                or type(reset["unit"].get("type")) is not str
                or not reset["unit"]["type"]
                or any(type(reset["unit"].get(field)) not in (int, float)
                       or not math.isfinite(reset["unit"][field])
                       for field in ("x", "y"))):
            errors.append("pending_build_plan_or_unit_projection")
        if type(before["tick"]) not in (int, float) or type(reset["tick"]) not in (int, float):
            errors.append("invalid_tick")
        elif not math.isfinite(before["tick"]) or not math.isfinite(reset["tick"]):
            errors.append("invalid_tick")
        elif reset["tick"] < before["tick"]:
            errors.append("nonmonotonic_tick")
        if original_tiles[TARGET]["block"] != "air":
            errors.append("pre_task_target_not_empty")
        if reset_tiles != original_tiles:
            errors.append("guard_projection_not_restored")
        if type(before["copper"]) is not int or reset["copper"] != before["copper"]:
            errors.append("canonical_copper_not_restored")
        if (reset["core_x"], reset["core_y"]) != (before["core_x"], before["core_y"]):
            errors.append("core_location_changed")
        if before["source_item"] != "copper" or reset["source_item"] != "copper":
            errors.append("copper_source_invalid")
    except (KeyError, TypeError, ValueError) as error:
        errors.append(str(error))
    return {"verified": not errors, "errors": errors,
            "authority": "private reset audit only; never controller-visible"}


def score_receipt(task_id: str, evaluation: dict) -> dict:
    """Create the only admissible success receipt after independent exact score."""
    if task_id not in {"A1", "A2", "A3", "B1", "B2", "B3"}:
        raise ValueError("unknown preregistered task id")
    required_fields = {"status", "contract_satisfied", "wrong_target",
                       "collateral_tiles", "source_preserved", "core_preserved",
                       "copper_delta", "paused_idle_completion", "guard_tiles", "scope"}
    if type(evaluation) is not dict or set(evaluation) != required_fields:
        raise ValueError("exact independent single-tile evaluation required")
    if (evaluation["status"] != "VERIFIED"
            or evaluation["contract_satisfied"] is not True
            or evaluation["wrong_target"] is not False
            or evaluation["collateral_tiles"] != []
            or evaluation["source_preserved"] is not True
            or evaluation["core_preserved"] is not True
            or type(evaluation["copper_delta"]) is not int
            or evaluation["copper_delta"] != -1
            or evaluation["paused_idle_completion"] is not True
            or type(evaluation["guard_tiles"]) is not int
            or evaluation["guard_tiles"] != len(GUARD)
            or evaluation["scope"] != EXPECTED_SCORE_SCOPE):
        raise ValueError("independent positive task score required before reset")
    epoch = ["A1", "A2", "A3", "B1", "B2", "B3"].index(task_id) + 1
    return {"filename": f"score-pass-{epoch}.receipt",
            "content": f"independent exact score verified for {task_id}\n",
            "authority": "private benchmark control; not controller-visible"}


def reset_witness_receipt(task_id: str, audit: dict) -> dict:
    """Release the next task only after exact independent reset verification."""
    if task_id not in {"A1", "A2", "A3", "B1", "B2", "B3"}:
        raise ValueError("unknown preregistered task id")
    if (type(audit) is not dict or set(audit) != {"verified", "errors", "authority"}
            or audit["verified"] is not True or audit["errors"] != []
            or audit["authority"] != "private reset audit only; never controller-visible"):
        raise ValueError("positive exact reset witness audit required")
    epoch = ["A1", "A2", "A3", "B1", "B2", "B3"].index(task_id) + 1
    return {"filename": f"reset-{epoch}.verified",
            "content": f"independent reset witness verified for {task_id}\n",
            "authority": "private benchmark control; not controller-visible"}


def reset_failure_receipt(task_id: str, audit: dict) -> dict:
    """Fail closed without advancing when the private reset audit fails."""
    if task_id not in {"A1", "A2", "A3", "B1", "B2", "B3"}:
        raise ValueError("unknown preregistered task id")
    if (type(audit) is not dict or set(audit) != {"verified", "errors", "authority"}
            or audit["verified"] is not False or type(audit["errors"]) is not list
            or not audit["errors"]
            or audit["authority"] != "private reset audit only; never controller-visible"):
        raise ValueError("negative exact reset witness audit required")
    epoch = ["A1", "A2", "A3", "B1", "B2", "B3"].index(task_id) + 1
    return {"filename": f"reset-{epoch}.fail",
            "content": f"reset witness failed for {task_id}; next task forbidden\n",
            "authority": "private benchmark control; not controller-visible"}


def geometry_receipt(before_binding: dict, after_binding: dict) -> dict:
    """Release B1 only after same-surface, changed-geometry host verification."""
    if type(before_binding) is not dict or type(after_binding) is not dict:
        raise ValueError("before and after pointer bindings required")
    before_surface, after_surface = before_binding.get("surface"), after_binding.get("surface")
    before_geometry, after_geometry = (before_binding.get("geometry"),
                                        after_binding.get("geometry"))
    if type(before_surface) not in (int, str) or before_surface in (0, ""):
        raise ValueError("nonzero original surface required")
    if after_surface != before_surface:
        raise ValueError("surface identity must be preserved across layout change")
    for geometry in (before_geometry, after_geometry):
        if (type(geometry) is not list or len(geometry) != 4
                or any(type(value) is not int for value in geometry)
                or geometry[2] <= 0 or geometry[3] <= 0):
            raise ValueError("four-integer positive surface geometry required")
    if before_geometry == after_geometry:
        raise ValueError("A-to-B surface geometry must change")
    return {"filename": "geometry-4.receipt",
            "content": "same surface; A-to-B geometry mutation verified\n",
            "authority": "private benchmark control; not controller-visible"}
