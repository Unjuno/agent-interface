#!/usr/bin/env python3
"""Deterministically create candidate-visible and oracle-only packed fixtures."""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).parent
N_PER_STRATUM = 200
COHORTS = 20_000
SEED = 8_049_001


def generate() -> tuple[dict, dict]:
    rng = random.Random(SEED)
    public_rows, oracle_rows = [], []
    for cohort in range(COHORTS):
        pub, oracle = {"cohort": cohort, "strata": {}}, {"cohort": cohort, "strata": {}}
        for name, p, q in (("A", 0.40, 0.25), ("B", 0.10, 0.75)):
            ymask = rmask = 0
            for i in range(N_PER_STRATUM):
                y = rng.random() < p
                resolved = rng.random() < q
                ymask |= int(y) << i
                rmask |= int(resolved) << i
            width = (N_PER_STRATUM + 3) // 4
            pub["strata"][name] = {
                "resolved_mask": f"{rmask:0{width}x}",
                "resolved_error_mask": f"{(ymask & rmask):0{width}x}",
            }
            oracle["strata"][name] = {"outcome_mask": f"{ymask:0{width}x}"}
        public_rows.append(pub)
        oracle_rows.append(oracle)
    return (
        {"schema": "unjuno.issue8049.public.v1", "cohorts": public_rows},
        {"schema": "unjuno.issue8049.oracle.v1", "cohorts": oracle_rows},
    )


def write_fixtures() -> None:
    public, oracle = generate()
    (ROOT / "public_input.json").write_text(json.dumps(public, separators=(",", ":")) + "\n")
    (ROOT / "oracle_input.json").write_text(json.dumps(oracle, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    write_fixtures()
