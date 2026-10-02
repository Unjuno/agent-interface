"""Validate one-generation palette+world coordinates for this fixed task."""


def validate(value, width: int, height: int) -> dict:
    required = {"op", "point_space", "points", "motion_model", "confidence_basis"}
    if type(value) is not dict or set(value) != required:
        raise ValueError("exact bounded task-point fields required")
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError("positive source image dimensions required")
    points = value["points"]
    if type(points) is not list or len(points) not in (0, 2):
        raise ValueError("target decision requires zero or exactly two points")
    if value["op"] == "needs_decision":
        if points or value["point_space"] != "not_applicable" or value["motion_model"] != "not_applicable":
            raise ValueError("safe stop must have no executable points")
        if value["confidence_basis"] not in ("no_candidate", "ambiguous", "unreadable"):
            raise ValueError("typed safe-stop basis required")
        return {"status": "NEEDS_DECISION", "reason": value["confidence_basis"], "points": []}
    if value["op"] != "target_reference" or len(points) != 2:
        raise ValueError("positive result requires palette then world target")
    if (value["point_space"] != "source_observation_pixels" or
            value["motion_model"] != "surface_origin_translation" or
            value["confidence_basis"] != "visually_unambiguous"):
        raise ValueError("positive points must be source-bound and unambiguous")
    checked = []
    for raw in points:
        if type(raw) is not dict or set(raw) != {"x", "y"}:
            raise ValueError("exact integer point required")
        if type(raw["x"]) is not int or type(raw["y"]) is not int:
            raise ValueError("integer coordinates required")
        if not 0 <= raw["x"] < width or not 0 <= raw["y"] < height:
            raise ValueError("point outside source observation")
        checked.append([raw["x"], raw["y"]])
    if checked[0] == checked[1]:
        raise ValueError("palette and world target points must differ")
    return {"status": "DIRECT", "palette_point": checked[0],
            "target_point": checked[1], "points": checked}
