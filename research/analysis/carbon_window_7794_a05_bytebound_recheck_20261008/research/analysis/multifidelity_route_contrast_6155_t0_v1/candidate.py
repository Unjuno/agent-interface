#!/usr/bin/env python3
"""Seeded finite T0 generator; emits raw task-level and route-difference rows."""
import argparse
import json
import math
import random

CASES = {"shared_level_only": 0.0, "delta_positive": 0.8, "delta_negative": -0.8}
KS = (1, 5, 20)
BLOCKS = 300
PILOT_N = 64
PAIRED_PER_COHORT = 20
EXTRA_X_PER_COHORT = 80
HIGH_COST = 100
LOW_COST = 1
MU_Y = 0.2
MU_X = -0.1


def paired_row(rng, rho):
    z = rng.gauss(0.0, 10.0)
    base_noise_y = rng.gauss(0.0, 0.1)
    base_noise_x = rng.gauss(0.0, 0.1)
    q = rng.gauss(0.0, 1.0)
    ey = rng.gauss(0.0, 1.0)
    ex = rng.gauss(0.0, 1.0)
    if rho == 0.0:
        dy = MU_Y + ey
        dx = MU_X + ex
    else:
        dy = MU_Y + math.sqrt(abs(rho)) * q + math.sqrt(1.0 - abs(rho)) * ey
        dx = MU_X + math.copysign(math.sqrt(abs(rho)), rho) * q + math.sqrt(1.0 - abs(rho)) * ex
    y_base = z + base_noise_y
    x_base = z + base_noise_x
    return [dy, dx, y_base, x_base, y_base + dy, x_base + dx]


def one_block(case, k, block):
    rho = CASES[case]
    # Each (case, K, block) has an independent deterministic stream.
    rng = random.Random(6155_20261002 + block * 1009 + k * 100003 + list(CASES).index(case) * 10000019)
    pilot = [paired_row(rng, rho) for _ in range(PILOT_N)]
    scored = [paired_row(rng, rho) for _ in range(PAIRED_PER_COHORT * k)]
    extra_x = [MU_X + rng.gauss(0.0, 1.0) for _ in range(EXTRA_X_PER_COHORT * k)]
    y_only = [paired_row(rng, rho)[0] for _ in range(21 * k + 64)]
    budget_x = [MU_X + rng.gauss(0.0, 1.0) for _ in range(64)]
    return {
        "case": case, "k": k, "block": block,
        "pilot": pilot, "scored": scored, "extra_x": extra_x,
        "y_only": y_only, "budget_x": budget_x,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.output, "w", encoding="utf-8") as stream:
        for case in CASES:
            for k in KS:
                for block in range(BLOCKS):
                    stream.write(json.dumps(one_block(case, k, block), separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
