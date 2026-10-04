"""Resolve explicit-frame pointer intents against one fresh target binding."""
import copy

from coordinate_frame_transform_v1 import points, translation


FRAMED_POINTER = {"pointer_click_in_frame", "pointer_drag_in_frame"}
FRAMED_CONDITION = "local_target_guard_postcondition_in_frame"


def _binding(value):
    if type(value) is not dict or set(value) != {"focus", "surface", "geometry"}:
        raise ValueError("fresh exact target pointer binding required")
    if type(value["focus"]) is not int or value["focus"] in (0, 1):
        raise ValueError("target focus must identify a client")
    if type(value["surface"]) is not int or value["surface"] in (0, 1):
        raise ValueError("target surface must identify a client")
    geometry = value["geometry"]
    translation("window_content", geometry, geometry)
    return copy.deepcopy(value)


def _boxes(value, delta, name):
    if type(value) is not list or not value:
        raise ValueError(f"{name} must be a nonempty list")
    result = []
    for box in value:
        if type(box) is not list or len(box) != 4 or any(type(item) is not int for item in box):
            raise ValueError(f"{name} require [x,y,width,height] integers")
        if box[2] <= 0 or box[3] <= 0:
            raise ValueError(f"{name} dimensions must be positive")
        result.append([box[0] + delta[0], box[1] + delta[1], box[2], box[3]])
    return result


def _common(step):
    frame = step.get("coordinate_frame")
    source = step.get("source_geometry")
    if frame not in ("screen_chrome", "window_content"):
        raise ValueError("explicit supported coordinate_frame required")
    return frame, source


def resolve_program(steps, target_binding):
    """Return raw executable steps and auditable frame-resolution records."""
    if type(steps) is not list:
        raise ValueError("steps must be a list")
    target = _binding(target_binding)
    prepared = []
    records = []
    for index, original in enumerate(steps):
        if type(original) is not dict:
            prepared.append(copy.deepcopy(original))
            continue
        op = original.get("op")
        if op not in FRAMED_POINTER and op != FRAMED_CONDITION:
            prepared.append(copy.deepcopy(original))
            continue
        step = copy.deepcopy(original)
        frame, source = _common(step)
        delta = translation(frame, source, target["geometry"])
        if op == "pointer_click_in_frame":
            required = {"op", "coordinate_frame", "source_geometry", "x", "y"}
            allowed = required | {"button", "duration_ms"}
            if not required <= set(step) or not set(step) <= allowed:
                raise ValueError("invalid framed click fields")
            resolved = points([{"x": step.pop("x"), "y": step.pop("y")}], delta)[0]
            step.pop("coordinate_frame")
            step.pop("source_geometry")
            step["op"] = "pointer_click"
            step.update(resolved)
        elif op == "pointer_drag_in_frame":
            required = {"op", "coordinate_frame", "source_geometry", "points", "duration_ms"}
            allowed = required | {"button"}
            if not required <= set(step) or not set(step) <= allowed:
                raise ValueError("invalid framed drag fields")
            step["points"] = points(step["points"], delta)
            step.pop("coordinate_frame")
            step.pop("source_geometry")
            step["op"] = "pointer_drag"
        else:
            required = {"op", "coordinate_frame", "source_geometry", "target_boxes",
                        "guard_boxes"}
            if not required <= set(step):
                raise ValueError("invalid framed target-guard fields")
            step["target_boxes"] = _boxes(step["target_boxes"], delta, "target_boxes")
            step["guard_boxes"] = _boxes(step["guard_boxes"], delta, "guard_boxes")
            step.pop("coordinate_frame")
            step.pop("source_geometry")
            step["op"] = "local_target_guard_postcondition"
        prepared.append(step)
        records.append({"event": "coordinate_frame_resolved", "step": index,
            "source_operation": op, "operation": step["op"], "coordinate_frame": frame,
            "source_geometry": copy.deepcopy(source),
            "target_geometry": copy.deepcopy(target["geometry"]),
            "translation": delta, "target_focus": target["focus"],
            "target_surface": target["surface"],
            "authority": "resolution only; ordinary program admission and runtime binding checks remain required"})
    return prepared, records
