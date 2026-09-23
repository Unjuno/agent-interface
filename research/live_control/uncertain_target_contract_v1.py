"""Strict passive target-or-active-probe decision contract."""


def validate(value, width, height):
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError("positive integer image dimensions required")
    if not isinstance(value, dict):
        raise ValueError("decision object required")
    required = {"op", "point_space", "point", "points", "motion_model",
                "confidence_basis"}
    if set(value) != required:
        raise ValueError("invalid uncertainty decision fields")
    if value["point_space"] != "source_observation_pixels":
        raise ValueError("points must use source observation pixels")
    op = value.get("op")
    if op == "target_reference":
        if value["motion_model"] != "surface_origin_translation":
            raise ValueError("direct point must declare surface translation")
        if value["confidence_basis"] != "visually_unambiguous":
            raise ValueError("direct decision requires the fixed confidence basis")
        points = value["points"]
        if not isinstance(points, list) or len(points) != 3:
            raise ValueError("exactly three probe candidates required")
    elif op == "request_hover_probe":
        if value["point"] != {"x": 0, "y": 0}:
            raise ValueError("probe decision direct point must be zero sentinel")
        if value["motion_model"] != "not_applicable":
            raise ValueError("probe decision motion must be not applicable")
        if value["confidence_basis"] != "icons_ambiguous":
            raise ValueError("probe decision requires ambiguous basis")
        points = value["points"]
        if not isinstance(points, list) or len(points) != 3:
            raise ValueError("exactly three probe points required")
    else:
        raise ValueError("unknown uncertainty decision")
    normalized = []
    for point in points:
        if (not isinstance(point, dict) or set(point) != {"x", "y"}
                or type(point["x"]) is not int or type(point["y"]) is not int):
            raise ValueError("integer x/y point required")
        pair = [point["x"], point["y"]]
        if not (0 <= pair[0] < width and 0 <= pair[1] < height):
            raise ValueError("point outside source observation")
        normalized.append(pair)
    if len({tuple(point) for point in normalized}) != len(normalized):
        raise ValueError("probe points must be distinct")
    if op == "target_reference" and [value["point"]["x"], value["point"]["y"]] not in normalized:
        raise ValueError("direct point must be among probe candidates")
    return {"op": op, "points": normalized,
            "requires_probe": op == "request_hover_probe"}
