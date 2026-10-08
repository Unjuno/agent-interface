#!/usr/bin/env python3
"""Generate the fresh, deterministic, typed synthetic allocation dataset."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 49720261006
STRATA = ("fresh_valid", "stale", "ambiguous", "forced_yield")
PER_STRATUM = 256


def build_rows():
    rng = random.Random(SEED)
    rows = []
    for stratum in STRATA:
        for j in range(PER_STRATUM):
            current = rng.randrange(10_000, 1_000_000)
            confidence = rng.randrange(0, 1001)
            stale = stratum == "stale"
            rows.append({
                "id": f"{stratum}-{j:04d}",
                "stratum": stratum,
                "confidence_milli": confidence,
                "observed_sequence": current - 1 if stale else current,
                "current_sequence": current,
                "ambiguous": stratum == "ambiguous",
                "forced_yield": stratum == "forced_yield",
            })
    rng.shuffle(rows)
    return rows


def main():
    path = ROOT / "dataset.json"
    if path.exists():
        raise SystemExit("STOP: dataset already exists; never overwrite a frozen allocation")
    doc = {"schema": "gpu-supervisor-transfer-break-even-dataset-v1",
           "seed": SEED, "rows": build_rows()}
    path.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"created {len(doc['rows'])} rows at {path.name}")


if __name__ == "__main__":
    main()

