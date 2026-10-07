"""Strict two-point output for the genuine batched plain reference arm."""


def _point(value, name):
    if type(value) is not dict or set(value) != {"point_space", "point"}:
        raise ValueError("exact plain " + name + " contract required")
    if value["point_space"] != "source_observation_pixels":
        raise ValueError("source observation pixel space required")
    point = value["point"]
    if (type(point) is not dict or set(point) != {"x", "y"}
            or any(type(point[key]) is not int for key in ("x", "y"))
            or not 0 <= point["x"] < 1280 or not 0 <= point["y"] < 800):
        raise ValueError("bounded integer source point required")
    return [point["x"], point["y"]]


def validate(value):
    if type(value) is not dict or set(value) != {"format", "field", "submit"}:
        raise ValueError("exact plain form points required")
    if value["format"] != "plain-form-points-v1":
        raise ValueError("plain form points v1 required")
    field = _point(value["field"], "field")
    submit = _point(value["submit"], "submit")
    if field == submit:
        raise ValueError("field and submit points must differ")
    return {"field_point": field, "submit_point": submit}
