"""Validate mutually exclusive direct, probe and coordinate-free target outcomes."""


def validate(value, width, height):
    if not isinstance(value, dict): raise ValueError("object required")
    op = value.get("op")
    def point(raw):
        if not isinstance(raw, dict) or set(raw) != {"x", "y"} or any(type(raw[k]) is not int for k in ("x", "y")):
            raise ValueError("integer point required")
        result = [raw["x"], raw["y"]]
        if not 0 <= result[0] < width or not 0 <= result[1] < height: raise ValueError("point outside source observation")
        return result
    if op == "needs_decision":
        if set(value) != {"op", "reason"} or value["reason"] not in ("no_candidate", "ambiguous", "unreadable"):
            raise ValueError("coordinate-free bounded stop required")
        return {"status": "NEEDS_DECISION", "reason": value["reason"], "points": []}
    common = {"op", "point_space", "motion_model", "confidence_basis"}
    if value.get("point_space") != "source_observation_pixels" or value.get("motion_model") != "surface_origin_translation":
        raise ValueError("source-bound translation point required")
    if op == "target_reference":
        if set(value) != common | {"point"} or value["confidence_basis"] != "visually_unambiguous":
            raise ValueError("invalid direct target")
        return {"status": "DIRECT", "points": [point(value["point"])]}
    if op == "request_hover_probe":
        if set(value) != common | {"points"} or value["confidence_basis"] != "visual_probe_required":
            raise ValueError("invalid probe request")
        if not isinstance(value["points"], list) or not 1 <= len(value["points"]) <= 3:
            raise ValueError("one to three probe points required")
        points = [point(raw) for raw in value["points"]]
        if len({tuple(p) for p in points}) != len(points): raise ValueError("probe points must be distinct")
        return {"status": "PROBE", "points": points}
    raise ValueError("unsupported target outcome")
