"""Geometry-derived read-only road/owner preservation score."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "openttd_oracle"))
from score import score as road_score


def contract_from_baseline(baseline):
    for key in ("x", "y", "width"):
        if type(baseline.get(key)) is not int:
            raise ValueError("integer baseline x/y/width required")
    x, y, width = baseline["x"], baseline["y"], baseline["width"]
    if width <= 0 or x < 2 or y < 2 or x + 4 >= width:
        raise ValueError("baseline geometry cannot contain declared guard")
    target = [y * width + x + dx for dx in range(3)]
    forbidden = [(y + 1) * width + x + dx for dx in range(3)]
    guard = [
        (y + dy) * width + x + dx
        for dy in range(-2, 4)
        for dx in range(-2, 5)
    ]
    return {
        "x": x,
        "y": y,
        "width": width,
        "target": target,
        "forbidden": forbidden,
        "owner": 0,
        "guard": guard,
    }


def indexed(record, contract):
    if any(record.get(key) != contract[key] for key in ("x", "y", "width")):
        raise ValueError("observation geometry differs from baseline contract")
    guard = record.get("guard")
    if not isinstance(guard, list) or len(guard) != len(contract["guard"]):
        raise ValueError("exact guard neighborhood required")
    if {tile.get("id") for tile in guard} != set(contract["guard"]):
        raise ValueError("unexpected guard tile ids")
    if any(
        type(tile.get("id")) is not int
        or type(tile.get("road")) is not bool
        or type(tile.get("owner")) is not int
        for tile in guard
    ):
        raise ValueError("invalid guard types")
    result = {
        tile["id"]: {"road": tile["road"], "owner": tile["owner"]}
        for tile in guard
    }
    for tile in record.get("tiles", []):
        if tile.get("id") not in result:
            raise ValueError("target tile outside guard")
        if result[tile["id"]] != {
            "road": tile.get("road"),
            "owner": tile.get("owner"),
        }:
            raise ValueError("contradictory overlapping tile records")
    return result


def score(observation, baseline):
    contract = contract_from_baseline(baseline)
    before = indexed(baseline, contract)
    after = indexed(observation, contract)
    old = road_score(observation, contract)
    changed = [
        tile
        for tile in contract["guard"]
        if tile not in contract["target"] and before[tile] != after[tile]
    ]
    checks = {
        **old["checks"],
        "surrounding_road_owner_unchanged": not changed,
    }
    return {
        "success": all(checks.values()),
        "checks": checks,
        "changed_surrounding_tiles": changed,
        "legacy_success": old["success"],
        "contract": {
            "x": contract["x"],
            "y": contract["y"],
            "width": contract["width"],
            "target": contract["target"],
            "forbidden": contract["forbidden"],
            "owner": contract["owner"],
            "guard": contract["guard"],
        },
    }
