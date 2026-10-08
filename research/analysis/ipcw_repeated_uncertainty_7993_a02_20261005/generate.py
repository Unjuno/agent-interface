#!/usr/bin/env python3
"""Generate fixed-stratum public masks and oracle-only outcomes for A02."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent
N = 200
COHORTS = 20_000
SEED = 8_049_020


def generate():
    rng = random.Random(SEED)
    public, oracle = [], []
    for cohort in range(COHORTS):
        pub = {"cohort": cohort, "strata": {}}
        tru = {"cohort": cohort, "strata": {}}
        for name, p, q in (("A", 0.40, 0.25), ("B", 0.10, 0.75)):
            outcomes = resolved = 0
            for i in range(N):
                y = rng.random() < p
                r = rng.random() < q
                outcomes |= int(y) << i
                resolved |= int(r) << i
            width = (N + 3) // 4
            pub["strata"][name] = {
                "resolved_mask": f"{resolved:0{width}x}",
                "resolved_error_mask": f"{(outcomes & resolved):0{width}x}",
            }
            tru["strata"][name] = {"outcome_mask": f"{outcomes:0{width}x}"}
        public.append(pub)
        oracle.append(tru)
    return (
        {"schema": "unjuno.issue8049.public.a02.v1", "cohorts": public},
        {"schema": "unjuno.issue8049.oracle.a02.v1", "cohorts": oracle},
    )


def write():
    public, oracle = generate()
    (ROOT / "public_input.json").write_text(json.dumps(public, separators=(",", ":")) + "\n")
    (ROOT / "oracle_input.json").write_text(json.dumps(oracle, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    write()
