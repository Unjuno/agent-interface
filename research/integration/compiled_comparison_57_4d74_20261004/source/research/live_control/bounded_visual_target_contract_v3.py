"""Validate one nonredundant points array across direct, probe and stop outcomes."""


def validate(value, width, height):
    required = {"op", "point_space", "points", "motion_model", "confidence_basis"}
    if not isinstance(value, dict) or set(value) != required: raise ValueError("exact target result fields required")
    if not isinstance(value["points"], list) or len(value["points"]) > 3: raise ValueError("zero to three points required")
    points = []
    for raw in value["points"]:
        if not isinstance(raw, dict) or set(raw) != {"x", "y"} or any(type(raw[k]) is not int for k in ("x", "y")):
            raise ValueError("integer point required")
        point = [raw["x"], raw["y"]]
        if not 0 <= point[0] < width or not 0 <= point[1] < height: raise ValueError("point outside source observation")
        points.append(point)
    if len(set(map(tuple, points))) != len(points): raise ValueError("points must be distinct")
    op = value["op"]
    if op == "needs_decision":
        if points or value["point_space"] != "not_applicable" or value["motion_model"] != "not_applicable":
            raise ValueError("bounded stop must carry an empty point array")
        if value["confidence_basis"] not in ("no_candidate", "ambiguous", "unreadable"):
            raise ValueError("invalid bounded-stop basis")
        return {"status": "NEEDS_DECISION", "reason": value["confidence_basis"], "points": []}
    if value["point_space"] != "source_observation_pixels" or value["motion_model"] != "surface_origin_translation":
        raise ValueError("source-bound translation points required")
    if op == "target_reference" and len(points) == 1 and value["confidence_basis"] == "visually_unambiguous":
        return {"status": "DIRECT", "points": points}
    if op == "request_hover_probe" and 1 <= len(points) <= 3 and value["confidence_basis"] == "visual_probe_required":
        return {"status": "PROBE", "points": points}
    raise ValueError("outcome and point cardinality disagree")
