#!/usr/bin/env python3
"""Frozen synthetic preference-method candidate for Issue #7411 T0 A01."""
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "formal_01"
SEED = 7411001
DOSES = list(range(0, 25, 2))


def estimate_threshold(rows):
    bins = []
    for dose in DOSES:
        observed = [r["choice"] for r in rows if r["dose_seconds"] == dose and r["choice"] in ("FASTER", "SAME")]
        if not observed:
            bins.append([dose, 0, 0])
        else:
            bins.append([dose, sum(v == "FASTER" for v in observed), len(observed)])
    # Pool adjacent violators on the binomial proportions.
    blocks = []
    for dose, yes, n in bins:
        blocks.append({"lo": dose, "hi": dose, "yes": yes, "n": n})
        while len(blocks) > 1:
            a, b = blocks[-2], blocks[-1]
            ra = a["yes"] / a["n"] if a["n"] else 0.0
            rb = b["yes"] / b["n"] if b["n"] else 0.0
            if ra <= rb:
                break
            blocks[-2:] = [{"lo": a["lo"], "hi": b["hi"], "yes": a["yes"] + b["yes"], "n": a["n"] + b["n"]}]
    populated = [b for b in blocks if b["n"]]
    if not populated or populated[0]["yes"] / populated[0]["n"] >= 0.5 or populated[-1]["yes"] / populated[-1]["n"] < 0.5:
        return {"status": "UNKNOWN", "threshold_seconds": None, "support": len(populated)}
    crossing = next((b for b in populated if b["yes"] / b["n"] >= 0.5), None)
    if crossing is None or crossing["lo"] == populated[0]["lo"]:
        return {"status": "UNKNOWN", "threshold_seconds": None, "support": len(populated)}
    prev = max((b for b in populated if b["hi"] < crossing["lo"]), key=lambda b: b["hi"])
    return {"status": "ESTIMATED", "threshold_seconds": (prev["hi"] + crossing["lo"]) / 2, "support": len(populated)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    rows = []
    truths = []
    base_thresholds = [6 + (i % 9) for i in range(160)]
    rng.shuffle(base_thresholds)
    for person, base in enumerate(base_thresholds):
        for loc, offset in (("PLANNER_BOUNDARY", 0), ("LOCAL_PROCESSING", 4)):
            threshold = base + offset
            truths.append({"respondent": person, "location": loc, "threshold_seconds": threshold})
            for dose in DOSES:
                missing = rng.random() < 0.02
                tie = (not missing) and rng.random() < 0.08
                import math
                p = 1.0 / (1.0 + math.exp(-(dose - threshold) / 1.5))
                if rng.random() < 0.04:
                    p = 0.5
                choice = "MISSING" if missing else ("TIE" if tie else ("FASTER" if rng.random() < p else "SAME"))
                rows.append({"respondent": person, "location": loc, "dose_seconds": dose, "choice": choice,
                             "task_effect_equal": True, "safety_gate": "PASS"})
    estimates = {}
    for loc in ("PLANNER_BOUNDARY", "LOCAL_PROCESSING"):
        estimates[loc] = estimate_threshold([r for r in rows if r["location"] == loc])
    low_support = [{"respondent": i, "location": "LOW_SUPPORT", "dose_seconds": dose,
                    "choice": "SAME", "task_effect_equal": True, "safety_gate": "PASS"}
                   for i in range(20) for dose in (0, 2, 4, 6)]
    low_estimate = estimate_threshold(low_support)
    # Control preference is intentionally favorable but an objective regression bars adoption.
    gate_control = {"mean_preference_faster": 0.9, "task_effect_equal": False,
                    "safety_gate": "FAIL", "adoption_eligible": False}
    raw = {"schema": "issue-7411-t0-a01-raw-v1", "seed": SEED, "doses_seconds": DOSES,
           "rows": rows, "low_support_rows": low_support, "truths": truths,
           "correctness_regression_control": gate_control}
    raw_bytes = (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (OUT / "raw.json").write_bytes(raw_bytes)
    candidate = {"schema": "issue-7411-t0-a01-candidate-v1", "estimates": estimates,
                 "low_support_estimate": low_estimate, "correctness_regression_control": gate_control,
                 "raw_sha256": hashlib.sha256(raw_bytes).hexdigest()}
    (OUT / "candidate.json").write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"rows": len(rows), "low_support_rows": len(low_support), "estimates": estimates,
                      "low_support": low_estimate, "raw_sha256": candidate["raw_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
