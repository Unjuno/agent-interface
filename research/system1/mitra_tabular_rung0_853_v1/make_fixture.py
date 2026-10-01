#!/usr/bin/env python3
"""Deterministically write the Issue #853 Rung-0 numeric fixture."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
SEED = 853
N_SUPPORT = 256
N_QUERY = 1024
N_FEATURES = 8
CLASSES = [f"C{i}" for i in range(6)]


def write_csv(path: Path, rows: list[list[object]], header: list[str]) -> str:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rng = np.random.Generator(np.random.PCG64(SEED))
    support = rng.standard_normal((N_SUPPORT, N_FEATURES), dtype=np.float32)
    queries = rng.standard_normal((N_QUERY, N_FEATURES), dtype=np.float32)
    labels = np.asarray([CLASSES[i % len(CLASSES)] for i in range(N_SUPPORT)])
    features = [f"f{i}" for i in range(N_FEATURES)]
    support_rows = [list(map(float, row)) + [label] for row, label in zip(support, labels)]
    query_rows = [list(map(float, row)) for row in queries]
    support_sha = write_csv(ROOT / "support.csv", support_rows, features + ["label"])
    query_sha = write_csv(ROOT / "queries.csv", query_rows, features)
    freeze = {
        "schema": "issue-853-mitra-rung0-fixture-v1",
        "seed": SEED,
        "rng": "numpy.PCG64",
        "dtype": "float32 generated then serialized as Python float decimal",
        "support_rows": N_SUPPORT,
        "query_rows": N_QUERY,
        "feature_count": N_FEATURES,
        "class_ids": CLASSES,
        "support_csv_sha256": support_sha,
        "query_csv_sha256": query_sha,
    }
    (ROOT / "fixture_manifest.json").write_text(
        json.dumps(freeze, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(freeze, sort_keys=True))


if __name__ == "__main__":
    main()
