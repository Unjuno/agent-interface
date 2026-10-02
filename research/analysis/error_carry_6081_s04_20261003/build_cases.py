"""Create the frozen public request matrix for #6081 S04."""

from fractions import Fraction
import json
import sys
from pathlib import Path


RAYS = [
    ("exact-east", 1, 0),
    ("exact-northeast", 1, 1),
    ("shallow-positive", 7, 2),
    ("near-axis-positive", 8, 1),
    ("balanced-positive", 3, 2),
    ("steep-positive", 2, 7),
    ("reversed-x", -7, 2),
    ("reversed-y", 7, -2),
    ("shallow-negative", -7, -2),
    ("near-axis-negative", 1, -8),
    ("cardinal-west", -1, 0),
    ("zero", 0, 0),
]
ALPHABETS = {
    "cardinal4": [[1, 0], [0, 1], [-1, 0], [0, -1]],
    "eightway8": [[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]],
}
POLICIES = ["horizon_nearest", "independent_round", "error_carry", "no_continuation"]
HORIZONS = [1, 2, 3, 4, 5, 7, 8]
SEEDS = list(range(6101, 6109))


def _triplet(x, y):
    denominator = x.denominator * y.denominator // __import__("math").gcd(x.denominator, y.denominator)
    return [x.numerator * (denominator // x.denominator), y.numerator * (denominator // y.denominator), denominator]


def _normalized_ray(x, y, alphabet_id):
    x, y = Fraction(x), Fraction(y)
    if alphabet_id == "cardinal4":
        scale = abs(x) + abs(y)
    else:
        scale = max(abs(x), abs(y))
    if scale == 0:
        return Fraction(0), Fraction(0)
    return x / scale, y / scale


def build_cases():
    requests = []
    for alphabet_id, alphabet in ALPHABETS.items():
        combos = ["E", "N", "W", "S"] if alphabet_id == "cardinal4" else ["E", "NE", "N", "NW", "W", "SW", "S", "SE"]
        for ray_id, raw_x, raw_y in RAYS:
            x, y = _normalized_ray(raw_x, raw_y, alphabet_id)
            intent = _triplet(x, y)
            for horizon in HORIZONS:
                case_id = f"{alphabet_id}/{ray_id}/{horizon}"
                for policy in POLICIES:
                    for seed in SEEDS:
                        requests.append({
                            "request_id": f"primary/{case_id}/{policy}/{seed}",
                            "case_id": case_id,
                            "alphabet_id": alphabet_id,
                            "alphabet": alphabet,
                            "intent": intent,
                            "horizon": horizon,
                            "deadline_slots": horizon,
                            "max_abs_prefix_error": 1,
                            "policy": policy,
                            "seed": seed,
                            "calibration_id": "linear-v1",
                            "current_calibration_id": "linear-v1",
                            "required_combo": None,
                            "available_combos": combos,
                        })

    card = ALPHABETS["cardinal4"]
    common = {
        "alphabet_id": "cardinal4",
        "alphabet": card,
        "policy": "error_carry",
        "seed": 6101,
        "max_abs_prefix_error": 1,
        "calibration_id": "linear-v1",
        "current_calibration_id": "linear-v1",
        "required_combo": None,
        "available_combos": ["E", "N", "W", "S"],
    }
    requests.extend([
        {**common, "request_id": "control/unavailable-combo", "case_id": "control/unavailable-combo", "intent": [1, 1, 2], "horizon": 4, "deadline_slots": 4, "required_combo": "NE"},
        {**common, "request_id": "control/one-slot-deadline", "case_id": "control/one-slot-deadline", "intent": [3, 1, 4], "horizon": 4, "deadline_slots": 1},
        {**common, "request_id": "control/calibration-mismatch", "case_id": "control/calibration-mismatch", "intent": [3, 1, 4], "horizon": 4, "deadline_slots": 4, "current_calibration_id": "linear-v2"},
    ])
    return {
        "schema": "agent-interface.error-carry-6081-s04.public.v1",
        "alphabets": ALPHABETS,
        "rays": [{"ray_id": name, "raw_direction": [x, y]} for name, x, y in RAYS],
        "horizons": HORIZONS,
        "policies": POLICIES,
        "seeds": SEEDS,
        "requests": requests,
    }


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: build_cases.py cases.json")
    Path(argv[1]).write_text(json.dumps(build_cases(), sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
