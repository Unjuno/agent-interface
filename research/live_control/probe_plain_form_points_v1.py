"""Validator controls for the plain reference output."""

import json

from plain_form_points_v1 import validate


def main():
    valid = {"format": "plain-form-points-v1",
             "field": {"point_space": "source_observation_pixels",
                       "point": {"x": 226, "y": 401}},
             "submit": {"point_space": "source_observation_pixels",
                        "point": {"x": 376, "y": 401}}}
    assert validate(valid) == {"field_point": [226, 401], "submit_point": [376, 401]}
    invalid = [
        {**valid, "format": "compiled-form-grounding-v1"},
        {**valid, "method": {}},
        {**valid, "submit": valid["field"]},
        {**valid, "field": {**valid["field"], "point_space": "window_content"}},
        {**valid, "field": {**valid["field"], "point": {"x": 1280, "y": 1}}},
    ]
    for row in invalid:
        try:
            validate(row)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid plain points accepted")
    print(json.dumps({"passed": True, "valid": 1, "invalid": len(invalid)}))


if __name__ == "__main__":
    main()
