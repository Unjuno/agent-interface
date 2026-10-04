"""Explicit rebasing from full observation pixels to window-content pixels."""


def to_window_content(point, geometry):
    if (type(point) is not list or len(point) != 2 or
            any(type(value) is not int for value in point)):
        raise ValueError("grounding point must be an integer pair")
    if (type(geometry) is not list or len(geometry) != 4 or
            any(type(value) is not int for value in geometry)):
        raise ValueError("source pointer geometry required for point transform")
    return [point[0] - geometry[0], point[1] - geometry[1]]
