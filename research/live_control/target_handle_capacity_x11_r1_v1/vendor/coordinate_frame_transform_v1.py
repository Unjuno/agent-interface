"""Strict coordinate transforms for screen-fixed chrome and window content."""


def _geometry(value, name):
    if type(value) is not list or len(value) != 4 or any(type(item) is not int for item in value):
        raise ValueError(f"{name} must be [x,y,width,height] integers")
    x, y, width, height = value
    if width <= 0 or height <= 0:
        raise ValueError(f"{name} dimensions must be positive")
    return x, y, width, height


def translation(frame, source_geometry, target_geometry):
    """Return the declared translation for one coordinate frame."""
    source = _geometry(source_geometry, "source_geometry")
    target = _geometry(target_geometry, "target_geometry")
    if frame == "screen_chrome":
        return [0, 0]
    if frame == "window_content":
        return [target[0] - source[0], target[1] - source[1]]
    raise ValueError("frame must be screen_chrome or window_content")


def points(value, delta):
    """Translate exact integer x/y points without changing their order."""
    if type(value) is not list or not value:
        raise ValueError("points must be a nonempty list")
    if type(delta) is not list or len(delta) != 2 or any(type(item) is not int for item in delta):
        raise ValueError("delta must be [dx,dy] integers")
    result = []
    for point in value:
        if type(point) is not dict or set(point) != {"x", "y"}:
            raise ValueError("points require exact x/y fields")
        if type(point["x"]) is not int or type(point["y"]) is not int:
            raise ValueError("point coordinates must be integers")
        result.append({"x": point["x"] + delta[0], "y": point["y"] + delta[1]})
    return result


def transform(frame, source_geometry, target_geometry, value):
    """Translate points according to an explicit frame and two bindings."""
    delta = translation(frame, source_geometry, target_geometry)
    return {"frame": frame, "translation": delta, "points": points(value, delta)}
