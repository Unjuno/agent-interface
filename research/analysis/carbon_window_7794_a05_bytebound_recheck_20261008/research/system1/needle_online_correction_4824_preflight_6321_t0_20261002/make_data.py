"""Deterministically construct frozen role datasets; no model code or fitting."""
import json
import random
import argparse
from pathlib import Path

SEEDS = (2026100201, 2026100202, 2026100203)
FEATURE_COUNT = 8


def patterns(bit):
    return [[bit, *((mask >> i) & 1 for i in range(7))] for mask in range(128)]


def rows(seed, role, split, per_bit, offset):
    result = []
    role_code = 17 if role == "A" else 31
    for bit in (0, 1):
        values = patterns(bit)
        rng = random.Random(seed * role_code + bit)
        rng.shuffle(values)
        for i, features in enumerate(values[offset:offset + per_bit]):
            target = 0 if role == "A" else int(features[0] == 1)
            result.append({"id": f"{seed}:{role}:{split}:{bit}:{i}", "seed": seed,
                           "role": role, "split": split, "features": features, "label": target})
    rng.shuffle(result)
    return result


def build(seeds=SEEDS):
    all_seeds = []
    for seed in seeds:
        all_seeds.append({
            "seed": seed,
            "splits": {
                "a_support": rows(seed, "A", "a_support", 32, 0),
                "b_arrival": rows(seed, "B", "b_arrival", 4, 0),
                "a_heldout": rows(seed, "A", "a_heldout", 64, 32),
                "b_heldout": rows(seed, "B", "b_heldout", 64, 4),
            },
        })
    return {"schema": "unjuno.needle4824.label-preflight.v1", "seeds": all_seeds}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    out = Path(args.output)
    out.write_text(json.dumps(build(config["seeds"]), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
