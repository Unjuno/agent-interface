"""Strict model point contract with separate pixel space and motion semantics."""


POINT_SPACE = "source_observation_pixels"
MOTION_TO_FRAME = {
    "surface_origin_translation": "window_content",
    "screen_fixed": "screen_chrome",
}


def validate(value):
    if type(value) is not dict or set(value) != {
            "op", "point_space", "point", "motion_model"}:
        raise ValueError("exact point-target contract required")
    if value["op"] != "target_reference":
        raise ValueError("target_reference operation required")
    if value["point_space"] != POINT_SPACE:
        raise ValueError("source observation pixel space required")
    point = value["point"]
    if (type(point) is not dict or set(point) != {"x", "y"}
            or any(type(point[name]) is not int for name in ("x", "y"))):
        raise ValueError("integer x/y point required")
    if value["motion_model"] not in MOTION_TO_FRAME:
        raise ValueError("supported motion model required")


def runtime_reference(value):
    validate(value)
    return {
        "point": [value["point"]["x"], value["point"]["y"]],
        "coordinate_frame": MOTION_TO_FRAME[value["motion_model"]],
        "point_space": value["point_space"],
        "motion_model": value["motion_model"],
    }

