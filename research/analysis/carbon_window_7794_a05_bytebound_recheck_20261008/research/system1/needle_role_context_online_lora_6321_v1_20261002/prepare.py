"""Construct fresh, role-disjoint-within-task binary data for Issue #6354."""

from __future__ import annotations

import hashlib
import json
import random

SEEDS = (2026100204, 2026100205, 2026100206)


def patterns(bit: int) -> list[list[int]]:
    return [[bit, *((mask >> i) & 1 for i in range(7))] for mask in range(128)]


def permuted(seed: int, role: str, bit: int, split: str) -> list[list[int]]:
    result = patterns(bit)
    salt = sum((index + 1) * ord(char) for index, char in enumerate(role + split))
    random.Random(seed * 1000003 + salt * 97 + bit).shuffle(result)
    return result


def make_rows(seed: int, role: str, split: str, per_bit: int, start: int) -> list[dict]:
    if role not in ("A", "B"):
        raise ValueError(f"unknown role: {role}")
    target_role = role
    result = []
    for bit in (0, 1):
        selected = permuted(seed, role, bit, split)[start:start + per_bit]
        for index, features in enumerate(selected):
            result.append({"id": f"{seed}:{role}:{split}:{bit}:{index}", "seed": seed,
                           "role": role, "split": split, "features": features,
                           "label": 0 if target_role == "A" else features[0]})
    random.Random(seed + sum(map(ord, role + split))).shuffle(result)
    return result


def make_seed(seed: int) -> dict:
    splits = {}
    role_vectors: dict[str, set[tuple[int, ...]]] = {"A": set(), "B": set()}
    role_vectors: dict[str, set[tuple[int, ...]]] = {"A": set(), "B": set()}
    all_vectors = [(bit, tuple(row)) for bit in (0, 1) for row in patterns(bit)]
    for role, train_key, test_key, train_count, test_count in (
        ("A", "a_support", "a_heldout", 64, 128),
        ("B", "b_arrival", "b_heldout", 8, 128),
    ):
        role_order = list(all_vectors)
        random.Random(seed + (271 if role == "A" else 619)).shuffle(role_order)
        per_bit_train, per_bit_test = train_count // 2, test_count // 2
        train_vectors, test_vectors = [], []
        for bit in (0, 1):
            pool = [v for b, v in role_order if b == bit]
            needed = per_bit_train + per_bit_test
            if len(pool) < needed:
                raise ValueError(f"finite feature space exhausted for role={role}, bit={bit}")
            train_part, test_part = pool[:per_bit_train], pool[per_bit_train:needed]
            train_vectors.extend(train_part)
            test_vectors.extend(test_part)
        random.Random(seed + sum(map(ord, train_key))).shuffle(train_vectors)
        random.Random(seed + sum(map(ord, test_key))).shuffle(test_vectors)
        def rows(vectors: list[tuple[int, ...]], key: str) -> list[dict]:
            return [{"id": f"{seed}:{role}:{key}:{idx}", "seed": seed, "role": role,
                     "split": key, "features": list(vector),
                     "label": 0 if role == "A" else vector[0]}
                    for idx, vector in enumerate(vectors)]
        splits[train_key] = rows(train_vectors, train_key)
        splits[test_key] = rows(test_vectors, test_key)
        role_vectors[role] = set(train_vectors + test_vectors)
        role_vectors[role] = set(train_vectors + test_vectors)
        role_vectors[role] = set(train_vectors + test_vectors)
    a_train = {tuple(row["features"]) for row in splits["a_support"]}
    cross_role_overlap = len(role_vectors["A"] & role_vectors["B"])
    return {"seed": seed, "splits": splits,
            "cross_role_overlap_count": cross_role_overlap,
            "role_conflict_probe": {"features": [0] * 8, "a_label": 0, "b_label": 0}}


def build(seeds: tuple[int, ...] = SEEDS) -> dict:
    return {"schema": "unjuno.needle.role-context-online.v1",
            "feature_count": 8, "seeds": [make_seed(seed) for seed in seeds]}


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest_bytes(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("STOP_DATASET_OUTPUT_ALREADY_EXISTS")
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(build()))
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())
