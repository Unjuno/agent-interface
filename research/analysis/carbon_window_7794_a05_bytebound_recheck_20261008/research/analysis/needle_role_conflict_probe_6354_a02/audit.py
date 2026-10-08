"""Independent raw-only verifier for #6354 ambiguity-probe packets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_DATASET_SHA256 = "5865040abbc60d79f138e81bf7e06bf6f885e66b5e29c9810ea8f599bad77685"

def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def audit(dataset_path: Path, raw_path: Path,
          expected_dataset_sha256: str = EXPECTED_DATASET_SHA256) -> dict:
    dataset_bytes = dataset_path.read_bytes()
    raw_bytes = raw_path.read_bytes()
    dataset = json.loads(dataset_bytes)
    packet = json.loads(raw_bytes)
    errors: list[str] = []
    expected_digest = hashlib.sha256(canonical(dataset)).hexdigest()
    if expected_digest != expected_dataset_sha256:
        errors.append("dataset_digest")
    if packet.get("schema") != "unjuno.needle.role-conflict-probe.raw.v1":
        errors.append("packet_schema")
    if packet.get("source_dataset_sha256") != expected_digest:
        errors.append("source_dataset_sha256")

    source_seeds = dataset.get("seeds", [])
    raw_seeds = packet.get("seeds", [])
    expected_seed_ids = [item.get("seed") for item in source_seeds]
    if [item.get("seed") for item in raw_seeds] != expected_seed_ids:
        errors.append("seed_coverage_or_order")
    raw_by_seed = {item.get("seed"): item for item in raw_seeds}

    for source in source_seeds:
        seed_id = source.get("seed")
        probe = raw_by_seed.get(seed_id)
        if probe is None:
            continue
        if set(probe) != {"seed", "features", "a_label", "b_label", "cross_role_overlap_count"}:
            errors.append(f"{seed_id}:probe_fields")
            continue
        features = probe.get("features")
        if (not isinstance(features, list) or len(features) != 8
                or any(type(bit) is not int or bit not in (0, 1) for bit in features)):
            errors.append(f"{seed_id}:features")
            continue

        role_vectors: dict[str, set[tuple[int, ...]]] = {"A": set(), "B": set()}
        for rows in source.get("splits", {}).values():
            for row in rows:
                role = row.get("role")
                vector = row.get("features")
                if role in role_vectors and isinstance(vector, list) and len(vector) == 8:
                    role_vectors[role].add(tuple(vector))
        common = role_vectors["A"] & role_vectors["B"]
        if tuple(features) not in common:
            errors.append(f"{seed_id}:probe_not_shared")
        if features[0] != 1:
            errors.append(f"{seed_id}:probe_not_contradictory_input")
        expected_a, expected_b = 0, features[0]
        if probe.get("a_label") != expected_a or probe.get("b_label") != expected_b:
            errors.append(f"{seed_id}:target_formula")
        if probe.get("a_label") == probe.get("b_label"):
            errors.append(f"{seed_id}:labels_not_contradictory")
        if probe.get("cross_role_overlap_count") != len(common):
            errors.append(f"{seed_id}:overlap_count")

    return {
        "schema": "unjuno.needle.role-conflict-probe.audit.v1",
        "status": "PASS_PROBE_CONTRACT_SCOPED" if not errors else "FAIL_PROBE_CONTRACT",
        "seed_count": len(raw_seeds),
        "error_count": len(errors),
        "errors": errors,
        "source_dataset_sha256": expected_digest,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.dataset, args.raw)
    encoded = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("xb") as stream:
        stream.write(encoded)
    print(result["status"])
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
