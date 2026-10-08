"""Pure shape rules for deriving a bounded target region from a model point."""


OPERATION = "target_handle_mint_from_point"


def validate_step(step):
    required = {"op", "name", "coordinate_frame", "source_sequence", "point",
                "region_size", "ttl_ms", "freshness_ms", "search_radius",
                "allowed_transformations"}
    if set(step) != required:
        raise ValueError("invalid point-derived target fields")
    if type(step["name"]) is not str or not step["name"]:
        raise ValueError("nonempty target alias required")
    if step["coordinate_frame"] not in ("screen_chrome", "window_content"):
        raise ValueError("supported coordinate frame required")
    if type(step["source_sequence"]) is not int or step["source_sequence"] < 1:
        raise ValueError("positive source sequence required")
    if (type(step["point"]) is not list or len(step["point"]) != 2
            or any(type(value) is not int for value in step["point"])):
        raise ValueError("point must be two integers")
    size = step["region_size"]
    if (type(size) is not list or len(size) != 2
            or any(type(value) is not int for value in size)
            or any(value < 8 or value > 64 or value % 2 for value in size)):
        raise ValueError("region size must be even integers in 8..64")
    if type(step["ttl_ms"]) is not int or not 1 <= step["ttl_ms"] <= 300000:
        raise ValueError("ttl_ms must be 1..300000")
    if (type(step["freshness_ms"]) is not int
            or not 1 <= step["freshness_ms"] <= 5000):
        raise ValueError("freshness_ms must be 1..5000")
    if (type(step["search_radius"]) is not int
            or not 0 <= step["search_radius"] <= 64):
        raise ValueError("search_radius must be 0..64")
    allowed = step["allowed_transformations"]
    if (type(allowed) is not list or not allowed or len(set(allowed)) != len(allowed)
            or "window_translation" not in allowed
            or any(value not in ("window_translation", "local_translation")
                   for value in allowed)):
        raise ValueError("bounded allowed transformations required")


def derive(point, size):
    return {
        "box": [point[0] - size[0] // 2, point[1] - size[1] // 2,
                size[0], size[1]],
        "offset": [size[0] // 2, size[1] // 2],
    }


def patch(image, box):
    x, y, width, height = box
    if (x < 0 or y < 0 or x + width > image.width
            or y + height > image.height):
        raise ValueError("derived target region outside observation")
    return image.crop((x, y, x + width, y + height)).tobytes()
