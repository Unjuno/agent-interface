#!/usr/bin/env python3
"""Generate a frozen categorical failure-mode construction corpus."""
import argparse
import json
import random
from pathlib import Path


LABELS = ["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7"]
WEIGHTS = [500, 250, 120, 60, 30, 20, 10, 10]
WEIGHT_TOTAL = sum(WEIGHTS)
PROBABILITY = {label: weight / WEIGHT_TOTAL for label, weight in zip(LABELS, WEIGHTS)}
BASE_SEED = 5_665_001
REPLICATES = 200
TRAIN_N = 100
VALIDATION_N = 500
K = 20
TAXONOMY = "failure-taxonomy-v1"
STRATUM = "synthetic-iid-generator-v1"


def draw(rng, n, labels=LABELS, weights=WEIGHTS):
    return rng.choices(labels, weights=weights, k=n)


def clusters(case_id, n):
    return [f"{case_id}-unit-{i}" for i in range(n)]


def assess(train, validation, train_units, validation_units, planned_n,
           unknown_n, train_taxonomy, validation_taxonomy,
           train_stratum, validation_stratum):
    if planned_n != len(train) + unknown_n or unknown_n != 0:
        return {"disposition": "HOLD_NO_ELIGIBLE_DENOMINATOR"}
    if len(train_units) != len(train) or len(set(train_units)) != len(train_units):
        return {"disposition": "HOLD_NONEXCHANGEABLE"}
    if len(validation_units) != len(validation) or len(set(validation_units)) != len(validation_units):
        return {"disposition": "HOLD_NONEXCHANGEABLE"}
    if train_taxonomy != validation_taxonomy:
        return {"disposition": "HOLD_TAXONOMY_UNSTABLE"}
    if train_stratum != validation_stratum:
        return {"disposition": "HOLD_NONEXCHANGEABLE"}

    seen = set(train)
    frequency = {label: train.count(label) for label in seen}
    f1 = sum(count == 1 for count in frequency.values())
    gt = f1 / len(train)
    prefix_seen = set(train[:-K])
    new_in_tail = 0
    for label in train[-K:]:
        if label not in prefix_seen:
            new_in_tail += 1
            prefix_seen.add(label)
    last_k = new_in_tail / K
    exact_missing_mass = sum(probability for label, probability in PROBABILITY.items() if label not in seen)
    validation_new_rate = sum(label not in seen for label in validation) / len(validation)
    return {
        "disposition": "ELIGIBLE_IID",
        "n": len(train),
        "f1": f1,
        "gt_prediction": gt,
        "last_k_prediction": last_k,
        "true_missing_mass": exact_missing_mass,
        "validation_new_rate": validation_new_rate,
        "gt_abs_error_to_truth": abs(gt - exact_missing_mass),
        "last_k_abs_error_to_truth": abs(last_k - exact_missing_mass),
        "gt_abs_error_to_validation": abs(gt - validation_new_rate),
        "last_k_abs_error_to_validation": abs(last_k - validation_new_rate),
    }


def record(case_id, kind, rng, train_n, validation_n=VALIDATION_N,
           planned_n=None, unknown_n=0, train_taxonomy=TAXONOMY,
           validation_taxonomy=TAXONOMY, train_stratum=STRATUM,
           validation_stratum=STRATUM, correlated=False, shifted=False):
    if shifted:
        train = draw(rng, train_n)
        shifted_labels = LABELS + ["F8"]
        shifted_weights = [weight * 9 for weight in WEIGHTS] + [1000]
        validation = draw(rng, validation_n, shifted_labels, shifted_weights)
        validation_stratum = "synthetic-shifted-generator-v1"
    elif correlated:
        independent = draw(rng, max(1, train_n // 5))
        train = [label for label in independent for _ in range(5)][:train_n]
        validation = draw(rng, validation_n)
    else:
        train = draw(rng, train_n)
        validation = draw(rng, validation_n)

    if correlated:
        train_units = [f"{case_id}-cluster-{i // 5}" for i in range(len(train))]
    else:
        train_units = clusters(case_id + "-train", len(train))
    validation_units = clusters(case_id + "-validation", len(validation))
    if planned_n is None:
        planned_n = train_n
    candidate = assess(train, validation, train_units, validation_units, planned_n,
                       unknown_n, train_taxonomy, validation_taxonomy,
                       train_stratum, validation_stratum)
    return {
        "schema": "issue5665-t1-raw-v1",
        "case_id": case_id,
        "kind": kind,
        "seed": None,
        "train_planned_n": planned_n,
        "train_unknown_n": unknown_n,
        "train": train,
        "train_unit_ids": train_units,
        "validation_planned_n": validation_n,
        "validation_unknown_n": 0,
        "validation": validation,
        "validation_unit_ids": validation_units,
        "train_taxonomy": train_taxonomy,
        "validation_taxonomy": validation_taxonomy,
        "train_stratum": train_stratum,
        "validation_stratum": validation_stratum,
        "candidate": candidate,
    }


def run(out_path):
    rows = []
    for replicate in range(REPLICATES):
        seed = BASE_SEED + replicate
        rng = random.Random(seed)
        row = record(f"iid-{replicate:03d}", "iid", rng, TRAIN_N)
        row["seed"] = seed
        rows.append(row)

    cases = [
        ("correlated-duplicate", "correlated", BASE_SEED + 10_001,
         dict(train_n=100, planned_n=100, correlated=True)),
        ("taxonomy-split", "taxonomy_drift", BASE_SEED + 10_002,
         dict(train_n=100, validation_taxonomy="failure-taxonomy-v2")),
        ("distribution-shift", "distribution_shift", BASE_SEED + 10_003,
         dict(train_n=100, shifted=True)),
        ("missing-outcome", "missing_outcome", BASE_SEED + 10_004,
         dict(train_n=99, planned_n=100, unknown_n=1)),
    ]
    for case_id, kind, seed, kwargs in cases:
        rng = random.Random(seed)
        row = record(case_id, kind, rng, **kwargs)
        row["seed"] = seed
        rows.append(row)

    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"rows": len(rows), "iid_replicates": REPLICATES,
                      "controls": len(cases), "raw_path": str(target)}, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(args.out)

