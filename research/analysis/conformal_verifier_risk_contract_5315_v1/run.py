#!/usr/bin/env python3
"""Frozen standard-library Monte Carlo for Issue #5315's first unit."""
import argparse
import json
import math
import random
from pathlib import Path

SEED = 5315
ALPHA = 0.10
TRIALS = 10_000
SAMPLE_SIZES = (4, 10)
RAW_SCORE_THRESHOLD = 0.90


def threshold(scores, rank):
    if rank > len(scores):
        return math.inf
    return sorted(scores)[rank - 1]


def prediction_set(q, true_score, false_score, shift_detected=False):
    if shift_detected:
        return ["FAIL", "PASS"]
    result = []
    if true_score <= q:
        result.append("PASS")
    if false_score <= q:
        result.append("FAIL")
    return result


def metrics(prediction, truth="PASS"):
    singleton = len(prediction) == 1
    return {
        "true_included": truth in prediction,
        "singleton": singleton,
        "wrong_singleton": singleton and prediction[0] != truth,
        "set_size": len(prediction),
        "empty": not prediction,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    rng = random.Random(SEED)
    raw_path = args.out / "raw.jsonl"
    counts = {}
    with raw_path.open("x", encoding="utf-8") as raw:
        for n in SAMPLE_SIZES:
            plug_rank = math.ceil(n * (1 - ALPHA))
            conformal_rank = math.ceil((n + 1) * (1 - ALPHA))
            for trial in range(TRIALS):
                calibration_u = [rng.random() for _ in range(n)]
                calibration = [math.sqrt(u) for u in calibration_u]
                id_true_u, id_false_u, shift_true_u, shift_false_u = [rng.random() for _ in range(4)]
                tests = {
                    "id": {"true": math.sqrt(id_true_u), "false": math.sqrt(id_false_u)},
                    "shift": {"true": shift_true_u ** 0.25, "false": shift_false_u ** 0.25},
                }
                q = {
                    "raw": RAW_SCORE_THRESHOLD,
                    "plugin": threshold(calibration, plug_rank),
                    "conformal": threshold(calibration, conformal_rank),
                }
                outcomes = {}
                for condition, scores in tests.items():
                    outcomes[condition] = {}
                    for policy, cutoff in q.items():
                        p = prediction_set(cutoff, scores["true"], scores["false"])
                        outcomes[condition][policy] = metrics(p)
                    if condition == "shift":
                        outcomes[condition]["known_shift_contract"] = metrics(
                            prediction_set(q["conformal"], scores["true"], scores["false"], shift_detected=True)
                        )
                serialized_q = {name: (None if math.isinf(value) else value) for name, value in q.items()}
                row = {
                    "n": n,
                    "trial": trial,
                    "calibration_u": calibration_u,
                    "id_u": id_true_u,
                    "id_false_u": id_false_u,
                    "shift_u": shift_true_u,
                    "shift_false_u": shift_false_u,
                    "ranks": {"plugin": plug_rank, "conformal": conformal_rank},
                    "thresholds": serialized_q,
                    "outcomes": outcomes,
                }
                raw.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                for condition, policies in outcomes.items():
                    for policy, values in policies.items():
                        key = f"n{n}/{condition}/{policy}"
                        acc = counts.setdefault(key, {k: 0 for k in ("true_included", "singleton", "wrong_singleton", "set_size", "empty")})
                        for name, value in values.items():
                            acc[name] += int(value) if isinstance(value, bool) else value
    summary = {}
    for key, values in sorted(counts.items()):
        denom = TRIALS
        summary[key] = {
            "trials": denom,
            "true_inclusion_rate": values["true_included"] / denom,
            "singleton_rate": values["singleton"] / denom,
            "wrong_singleton_rate": values["wrong_singleton"] / denom,
            "mean_set_size": values["set_size"] / denom,
            "empty_rate": values["empty"] / denom,
        }
    receipt = {
        "allocation": "conformal-risk-5315-v01-20260930-01",
        "seed": SEED,
        "alpha": ALPHA,
        "trials_per_sample_size": TRIALS,
        "sample_sizes": list(SAMPLE_SIZES),
        "rows": TRIALS * len(SAMPLE_SIZES),
        "summary": summary,
    }
    (args.out / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": receipt["rows"], "summary": summary}, sort_keys=True))


if __name__ == "__main__":
    main()
