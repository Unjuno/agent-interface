"""Pure controls for the passive target-or-active-probe contract."""
import json

from uncertain_target_contract_v1 import validate


direct = {"op": "target_reference", "point_space": "source_observation_pixels",
          "point": {"x": 480, "y": 51},
          "points": [{"x": 456, "y": 51}, {"x": 480, "y": 51},
                     {"x": 504, "y": 51}],
          "motion_model": "surface_origin_translation",
          "confidence_basis": "visually_unambiguous"}
probe = {"op": "request_hover_probe", "point_space": "source_observation_pixels",
         "point": {"x": 0, "y": 0},
         "points": [{"x": 456, "y": 51}, {"x": 480, "y": 51},
                    {"x": 504, "y": 51}], "motion_model": "not_applicable",
         "confidence_basis": "icons_ambiguous"}
assert validate(direct, 1280, 800)["requires_probe"] is False
assert validate(probe, 1280, 800)["requires_probe"] is True
invalid = [None, {}, {**direct, "extra": 1}, {**direct, "point_space": "screen"},
           {**direct, "confidence_basis": "guess"},
           {**direct, "points": [{"x": 456, "y": 51}] * 3},
           {**direct, "point": {"x": 600, "y": 51}},
           {**probe, "points": probe["points"][:2]},
           {**probe, "points": [probe["points"][0]] * 3},
           {**probe, "motion_model": "surface_origin_translation"},
           {**probe, "points": [{"x": 456, "y": 51}, {"x": 480, "y": 51},
                                {"x": 2000, "y": 51}]}]
refused = 0
for value in invalid:
    try:
        validate(value, 1280, 800)
    except ValueError:
        refused += 1
    else:
        raise AssertionError("invalid uncertainty decision accepted")
print(json.dumps({"valid_direct": True, "valid_probe": True,
                  "invalid_decisions_refused": refused}))
