"""Geometry-derived read-only score for the five-tile L road objective."""


def contract_from_baseline(baseline):
    for key in ("x", "y", "width"):
        if type(baseline.get(key)) is not int:
            raise ValueError("integer baseline x/y/width required")
    x, y, width = baseline["x"], baseline["y"], baseline["width"]
    if width <= 0 or x < 2 or y < 2 or x + 6 >= width:
        raise ValueError("baseline geometry cannot contain declared L guard")
    tile = lambda dx, dy: (y + dy) * width + x + dx
    target = [tile(0, 0), tile(1, 0), tile(2, 0), tile(2, 1), tile(2, 2)]
    forbidden = [tile(0, 1), tile(1, 1), tile(0, 2), tile(1, 2)]
    guard = [tile(dx, dy) for dy in range(-2, 5) for dx in range(-2, 5)]
    return {"x": x, "y": y, "width": width, "target": target,
            "forbidden": forbidden, "owner": 0, "guard": guard}


def indexed(record, contract):
    if any(record.get(key) != contract[key] for key in ("x", "y", "width")):
        raise ValueError("observation geometry differs from baseline contract")
    guard = record.get("guard")
    if not isinstance(guard, list) or len(guard) != len(contract["guard"]):
        raise ValueError("exact guard neighborhood required")
    if {tile.get("id") for tile in guard} != set(contract["guard"]):
        raise ValueError("unexpected guard tile ids")
    if any(type(t.get("id")) is not int or type(t.get("road")) is not bool or type(t.get("owner")) is not int for t in guard):
        raise ValueError("invalid guard types")
    result = {t["id"]: {"road": t["road"], "owner": t["owner"]} for t in guard}
    expected_tiles = contract["target"] + contract["forbidden"]
    tiles = record.get("tiles")
    if not isinstance(tiles, list) or len(tiles) != len(expected_tiles) or {t.get("id") for t in tiles} != set(expected_tiles):
        raise ValueError("missing/duplicate/unexpected tile observation")
    for t in tiles:
        if result[t["id"]] != {"road": t.get("road"), "owner": t.get("owner")}:
            raise ValueError("contradictory overlapping tile records")
    return result


def score(observation, baseline):
    contract = contract_from_baseline(baseline)
    before, after = indexed(baseline, contract), indexed(observation, contract)
    desired = list(zip(contract["target"], contract["target"][1:]))
    edges = observation.get("edges")
    if not isinstance(edges, list) or len(edges) != len(desired) or [(e[0], e[1]) for e in edges if isinstance(e, list) and len(e) == 4] != desired:
        raise ValueError("missing or unexpected connection observation")
    if any(len(e) != 4 or type(e[2]) is not bool or type(e[3]) is not bool for e in edges):
        raise ValueError("invalid connection types")
    changed = [t for t in contract["guard"] if t not in contract["target"] and before[t] != after[t]]
    checks = {
        "target_owned_roads": all(after[t]["road"] and after[t]["owner"] == contract["owner"] for t in contract["target"]),
        "ordered_bidirectional_connections": all(e[2] and e[3] for e in edges),
        "forbidden_tiles_clear": not any(after[t]["road"] for t in contract["forbidden"]),
        "surrounding_road_owner_unchanged": not changed,
    }
    return {"success": all(checks.values()), "checks": checks,
            "changed_surrounding_tiles": changed, "contract": contract}
