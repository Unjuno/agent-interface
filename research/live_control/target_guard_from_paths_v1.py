"""Derive disjoint target/guard boxes from an admitted two-segment pointer plan."""


def _points(value, name):
    if type(value) is not list or not 2 <= len(value) <= 16:
        raise ValueError(f"{name} must contain 2..16 points")
    result = []
    for point in value:
        if type(point) is not dict or set(point) != {"x", "y"}:
            raise ValueError(f"{name} points require exact x/y fields")
        if type(point["x"]) is not int or type(point["y"]) is not int:
            raise ValueError(f"{name} coordinates must be integers")
        result.append((point["x"], point["y"]))
    if len(set(result)) != len(result):
        raise ValueError(f"{name} points must be distinct")
    return result


def _box(center, width, height):
    x, y = center
    return [x - width // 2, y - height // 2, width, height]


def _overlap(left, right):
    lx, ly, lw, lh = left
    rx, ry, rw, rh = right
    return lx < rx + rw and rx < lx + lw and ly < ry + rh and ry < ly + lh


def derive(first_path, continuation_path, box_width=12, box_height=8,
           shared_corner_tolerance=8):
    """Cover the first path and guard the unshared continuation path."""
    first = _points(first_path, "first_path")
    continuation = _points(continuation_path, "continuation_path")
    if type(box_width) is not int or type(box_height) is not int:
        raise ValueError("box dimensions must be integers")
    if not 2 <= box_width <= 128 or not 2 <= box_height <= 128:
        raise ValueError("box dimensions must be 2..128")
    if type(shared_corner_tolerance) is not int or not 0 <= shared_corner_tolerance <= 32:
        raise ValueError("shared corner tolerance must be 0..32")
    dx = abs(first[-1][0] - continuation[0][0])
    dy = abs(first[-1][1] - continuation[0][1])
    if max(dx, dy) > shared_corner_tolerance:
        raise ValueError("paths must share a bounded visual corner")
    target = [_box(point, box_width, box_height) for point in first]
    guard = [_box(point, box_width, box_height) for point in continuation[1:]]
    if any(_overlap(left, right) for index, left in enumerate(target + guard)
           for right in (target + guard)[index + 1:]):
        raise ValueError("derived boxes overlap")
    return {
        "target_boxes": target,
        "guard_boxes": guard,
        "derivation": {
            "format": "target-guard-from-pointer-paths-v1",
            "box_width": box_width,
            "box_height": box_height,
            "shared_corner_offset": [continuation[0][0] - first[-1][0],
                                     continuation[0][1] - first[-1][1]],
            "shared_corner_tolerance": shared_corner_tolerance,
            "guard_excludes_continuation_shared_corner": True,
        },
    }
