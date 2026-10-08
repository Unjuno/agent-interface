from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


DECISIONS = ("ACCEPT", "YIELD", "REJECT")


def summarize(path: Path) -> dict:
    groups = defaultdict(Counter)
    paired = defaultdict(Counter)
    seen = set()
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            key = (row["seed"], row["arm"], row["stratum"], row["case_id"])
            if key in seen:
                raise ValueError(f"duplicate prediction key: {key}")
            seen.add(key)
            decision = row["model_decision"]
            if decision not in DECISIONS:
                raise ValueError(f"invalid frozen model decision: {decision}")
            label = "positive" if row["label"] == 1 else "negative"
            groups[(row["arm"], row["stratum"], label)][decision] += 1
            if row["label"] == 1 and row["stratum"] in ("translation_a", "translation_b"):
                paired[(row["seed"], row["arm"])]["positive_accepts"] += int(decision == "ACCEPT")
    strata = {}
    for (arm, stratum, label), counts in sorted(groups.items()):
        strata[f"{arm}:{stratum}:{label}"] = {
            "rows": sum(counts.values()),
            "accept": counts["ACCEPT"], "yield": counts["YIELD"], "reject": counts["REJECT"],
            "accept_rate": counts["ACCEPT"] / sum(counts.values()) if counts else 0.0,
        }
    per_seed = {}
    for seed in sorted({key[0] for key in paired}):
        per_seed[str(seed)] = {
            arm: paired[(seed, arm)]["positive_accepts"] for arm in ("control", "treatment")
        }
    return {
        "schema": "tiny-visual-target-position-decision-rates-v1",
        "prediction_rows": len(seen),
        "thresholds": {"accept_min": 0.75, "yield_min": 0.25, "classification": 0.5},
        "stratum_label_rates": strata,
        "heldout_translation_positive_accepts_by_seed": per_seed,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = summarize(args.input)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    args.out.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()

