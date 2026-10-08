"""Create deterministic synthetic ordinal fixtures for Issue #8502 T0 A01."""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


CUTS = (-1.0, -0.3, 0.3, 1.0)
LOADINGS = (0.80,) * 6
FULL_N = 1500
SPARSE_N = 20
SEEDS = {"F01": 850201, "F02": 850202, "F03": 850203, "F04": 850204, "F05": 850205}
TRUTH = {
    "F01": {"expected": "COMPATIBLE_SCREEN", "localization": []},
    "F02": {"expected": "THRESHOLD_NONINVARIANCE", "localization": [2]},
    "F03": {"expected": "LOADING_PATTERN_NONINVARIANCE", "localization": [2]},
    "F04": {"expected": "STRUCTURE_NONINVARIANCE", "localization": []},
    "F05": {"expected": "UNCERTAIN", "localization": []},
}


def ordinal(value: float, cuts: tuple[float, ...]) -> int:
    return sum(value > cut for cut in cuts)


def group_rows(n: int, seed: int, *, group_b: bool, condition: str) -> list[list[int]]:
    rng = random.Random(seed)
    rows: list[list[int]] = []
    for _ in range(n):
        f1 = rng.gauss(0.0, 1.0)
        f2 = rng.gauss(0.0, 1.0) if group_b and condition == "structure" else f1
        row: list[int] = []
        for item in range(6):
            loading = LOADINGS[item]
            if group_b and condition == "loading" and item == 2:
                loading = 0.10
            factor = f1 if not (group_b and condition == "structure" and item >= 3) else f2
            residual = math.sqrt(1.0 - loading * loading)
            latent_response = loading * factor + residual * rng.gauss(0.0, 1.0)
            cuts = CUTS
            if group_b and condition == "threshold" and item == 2:
                cuts = tuple(cut + 0.65 for cut in CUTS)
            row.append(ordinal(latent_response, cuts))
        rows.append(row)
    return rows


def build(pilot: bool = False) -> tuple[dict, dict]:
    fixtures = []
    truth = {"schema": "issue8502-t0-a01-truth-v1", "cases": {}}
    for fixture_id, condition in (("F01", "invariant"), ("F02", "threshold"), ("F03", "loading"), ("F04", "structure"), ("F05", "invariant")):
        n = 20 if fixture_id == "F05" else (600 if pilot else FULL_N)
        seed = SEEDS[fixture_id] + (700000 if pilot else 0)
        fixtures.append({
            "fixture_id": fixture_id,
            "groups": {
                "A": group_rows(n, seed, group_b=False, condition=condition),
                "B": group_rows(n, seed + 1009, group_b=True, condition=condition),
            },
        })
        truth["cases"][fixture_id] = TRUTH[fixture_id]
    return {"schema": "issue8502-t0-a01-ordinal-fixtures-v1", "item_count": 6, "category_count": 5, "fixtures": fixtures}, truth


def dump(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", action="store_true", help="emit a separate 600/group construction fixture to stdout")
    args = parser.parse_args()
    fixtures, truth = build(pilot=args.pilot)
    if args.pilot:
        print(dump({"fixtures": fixtures, "truth": truth}).decode("utf-8"))
        return
    root = Path(__file__).resolve().parent
    for name, payload in (("fixtures.json", fixtures), ("truth.json", truth)):
        with (root / name).open("xb") as stream:
            stream.write(dump(payload))
    print(json.dumps({"generated": ["fixtures.json", "truth.json"], "fixture_count": len(fixtures["fixtures"]), "formal_seed_set": True}, sort_keys=True))


if __name__ == "__main__":
    main()
