"""Build a corrected ambiguity-probe packet without changing frozen data."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_DATASET_SHA256 = "5865040abbc60d79f138e81bf7e06bf6f885e66b5e29c9810ea8f599bad77685"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def load(path: Path) -> tuple[dict, str]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict) or not isinstance(value.get("seeds"), list):
        raise ValueError("dataset_schema")
    digest = hashlib.sha256(canonical(value)).hexdigest()
    if digest != EXPECTED_DATASET_SHA256:
        raise ValueError("STOP_DATASET_DIGEST_MISMATCH")
    return value, digest


def vectors(seed: dict, role: str) -> set[tuple[int, ...]]:
    result: set[tuple[int, ...]] = set()
    for split, rows in seed.get("splits", {}).items():
        if not split.startswith(role.lower() + "_") or not isinstance(rows, list):
            continue
        for row in rows:
            features = row.get("features")
            if (isinstance(features, list) and len(features) == 8
                    and all(type(bit) is int and bit in (0, 1) for bit in features)):
                result.add(tuple(features))
    return result


def build(dataset: dict, source_sha256: str) -> dict:
    rows = []
    for seed in dataset["seeds"]:
        a_vectors = vectors(seed, "A")
        b_vectors = vectors(seed, "B")
        candidates = sorted(vector for vector in a_vectors & b_vectors if vector[0] == 1)
        if not candidates:
            raise ValueError(f"no_positive_bit0_overlap:{seed.get('seed')}")
        features = list(candidates[0])
        rows.append({
            "seed": seed["seed"],
            "features": features,
            "a_label": 0,
            "b_label": features[0],
            "cross_role_overlap_count": len(a_vectors & b_vectors),
        })
    return {
        "schema": "unjuno.needle.role-conflict-probe.raw.v1",
        "source_dataset_sha256": source_sha256,
        "seeds": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    dataset, source_sha256 = load(args.dataset)
    raw = canonical(build(dataset, source_sha256))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("xb") as stream:
        stream.write(raw)
    print(hashlib.sha256(raw).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
