"""Deterministic controls for separated point-space and motion semantics."""
from point_target_contract_v2 import runtime_reference, validate


def main():
    valid = {"op": "target_reference",
             "point_space": "source_observation_pixels",
             "point": {"x": 270, "y": 243},
             "motion_model": "surface_origin_translation"}
    validate(valid)
    assert runtime_reference(valid) == {
        "point": [270, 243], "coordinate_frame": "window_content",
        "point_space": "source_observation_pixels",
        "motion_model": "surface_origin_translation"}
    fixed = {**valid, "motion_model": "screen_fixed"}
    assert runtime_reference(fixed)["coordinate_frame"] == "screen_chrome"
    invalid = [
        {**valid, "extra": True},
        {**valid, "op": "pointer_click"},
        {**valid, "point_space": "window_content"},
        {**valid, "point": {"x": 270}},
        {**valid, "point": {"x": True, "y": 243}},
        {**valid, "motion_model": "window_content"},
    ]
    for value in invalid:
        try:
            validate(value)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid point-target contract accepted")
    print("point_target_contract_v2_probe_passed")


if __name__ == "__main__":
    main()
