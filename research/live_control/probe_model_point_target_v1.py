"""Deterministic controls for point-derived target shape rules."""
from PIL import Image

from model_point_target_v1 import OPERATION, derive, patch, validate_step


def main():
    valid = {"op": OPERATION, "name": "save_form",
             "coordinate_frame": "window_content", "source_sequence": 7,
             "point": [290, 252], "region_size": [24, 14],
             "ttl_ms": 60000, "freshness_ms": 1000, "search_radius": 0,
             "allowed_transformations": ["window_translation"]}
    validate_step(valid)
    assert derive(valid["point"], valid["region_size"]) == {
        "box": [278, 245, 24, 14], "offset": [12, 7]}
    image = Image.new("RGB", (400, 300), "white")
    assert len(patch(image, [278, 245, 24, 14])) == 24 * 14 * 3
    invalid = [
        {**valid, "extra": 1}, {**valid, "name": ""},
        {**valid, "source_sequence": 0}, {**valid, "point": [290, True]},
        {**valid, "region_size": [23, 14]}, {**valid, "region_size": [6, 14]},
        {**valid, "ttl_ms": 0}, {**valid, "freshness_ms": 5001},
        {**valid, "search_radius": 65},
        {**valid, "allowed_transformations": ["local_translation"]},
    ]
    for candidate in invalid:
        try:
            validate_step(candidate)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid point-derived target accepted")
    try:
        patch(image, [-1, 245, 24, 14])
    except ValueError:
        pass
    else:
        raise AssertionError("outside patch accepted")
    print("model_point_target_v1_probe_passed")


if __name__ == "__main__":
    main()
