"""Bind a coarse model point only to a nearby fresh screen-derived palette slot."""
import math


def bind(point, slots, maximum_distance=48):
    if len(point) != 2 or any(type(value) is not int for value in point):
        raise ValueError("integer coarse point required")
    ranked = sorted((math.hypot(point[0] - slot["point"][0], point[1] - slot["point"][1]), slot)
                    for slot in slots)
    distance, slot = ranked[0]
    if distance > maximum_distance:
        return {"status": "NEEDS_DECISION", "reason": "coarse_point_outside_palette_neighbourhood",
                "coarse_point": point, "nearest_distance": distance, "point": None}
    return {"status": "BOUND", "coarse_point": point, "nearest_distance": distance,
            "row": slot["row"], "column": slot["column"], "point": slot["point"]}
