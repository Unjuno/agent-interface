"""Strict semantic/point contract for the first compiled-form live block."""


def _target(value, name):
    if type(value) is not dict or set(value) != {
            "point_space", "point", "motion_model"}:
        raise ValueError(f"exact {name} target contract required")
    if value["point_space"] != "source_observation_pixels":
        raise ValueError("source observation pixel space required")
    if value["motion_model"] != "surface_origin_translation":
        raise ValueError("surface origin translation required")
    point = value["point"]
    if (type(point) is not dict or set(point) != {"x", "y"} or
            any(type(point[key]) is not int for key in ("x", "y")) or
            not 0 <= point["x"] < 1280 or not 0 <= point["y"] < 800):
        raise ValueError("bounded integer source point required")
    return [point["x"], point["y"]]


def validate(value):
    if type(value) is not dict or set(value) != {"format", "field", "submit", "method"}:
        raise ValueError("exact compiled form grounding required")
    if value["format"] != "compiled-form-grounding-v1":
        raise ValueError("compiled form grounding v1 required")
    field = _target(value["field"], "field")
    submit = _target(value["submit"], "submit")
    if field == submit:
        raise ValueError("field and submit points must differ")
    method = value["method"]
    expected = {
        "first_action": "enter_exact_token",
        "continue_when": "field_pixels_changed_and_submit_revalidated",
        "second_action": "activate_submit",
        "complete_when": "submission_pixels_changed_then_independent_score",
    }
    if method != expected:
        raise ValueError("exact bounded method declaration required")
    return {"field_point": field, "submit_point": submit,
            "method": method.copy()}
