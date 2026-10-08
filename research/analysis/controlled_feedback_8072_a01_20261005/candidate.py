#!/usr/bin/env python3
"""Deterministic finite simulation for Issue #8072; standard library only."""
import json
import random
import sys

SEEDS = 100
DEV_N = 16
FRESH_N = 128
QUERIES = 8
THRESHOLD_ROWS = 2


def cohort(seed, n, salt):
    rng = random.Random(seed * 1009 + salt)
    return [{"id": f"{salt}:{i}", "stratum": rng.randrange(4),
             "truth": rng.randrange(2), "baseline": None} for i in range(n)]


def build(seed):
    dev = cohort(seed, DEV_N, 1)
    fresh = cohort(seed, FRESH_N, 2)
    # Exactly half of each cohort starts correct; deterministic tie handling.
    for rows in (dev, fresh):
        for i, row in enumerate(rows):
            row["baseline"] = row["truth"] if i % 2 == 0 else 1 - row["truth"]
    return dev, fresh


def score(rows, patches, strata):
    correct = 0
    for row in rows:
        pred = row["baseline"]
        if row["id"] in patches or row["stratum"] in strata:
            pred = row["truth"]
        correct += pred == row["truth"]
    return correct


def run_arm(seed, arm):
    dev, fresh = build(seed)
    patches, strata, queries = set(), set(), []
    locked = False
    safety_vetoes = 0
    for q in range(QUERIES):
        current = score(dev, patches, strata)
        if arm == "FULL":
            # Detailed feedback targets the first remaining failed row.
            failing = next((r for r in dev if score([r], patches, strata) == 0), None)
            proposal = {"kind": "PATCH_ID", "target": failing["id"] if failing else None}
        else:
            # Aggregate-only feedback cannot identify a row; it cycles strata.
            proposal = {"kind": "TRANSFER_STRATUM", "target": q % 4}
        trial_patches, trial_strata = set(patches), set(strata)
        if proposal["kind"] == "PATCH_ID" and proposal["target"] is not None:
            trial_patches.add(proposal["target"])
        elif proposal["kind"] == "TRANSFER_STRATUM":
            trial_strata.add(proposal["target"])
        proposed = score(dev, trial_patches, trial_strata)
        hard_failure = (q == 6)  # planted independent hard-safety regression
        feedback = {"utility_rows": proposed-current} if arm == "FULL" else {
            "accepted_threshold": proposed-current >= THRESHOLD_ROWS}
        veto = hard_failure
        accept = (not veto and (proposed-current >= THRESHOLD_ROWS if arm == "CONTROLLED"
                                else proposed > current))
        if accept:
            patches, strata = trial_patches, trial_strata
        queries.append({"q": q, "proposal": proposal, "before": current,
                        "proposed": proposed, "hard_failure": hard_failure,
                        "exact_safety_disclosed": True, "veto": veto,
                        "feedback": feedback, "accepted": accept,
                        "fresh_read": False})
    locked = True
    return {"seed": seed, "arm": arm, "queries": queries, "locked_before_fresh": locked,
            "dev_correct": score(dev, patches, strata), "dev_n": len(dev),
            "fresh_correct": score(fresh, patches, strata), "fresh_n": len(fresh),
            "patches": sorted(patches), "strata": sorted(strata),
            "post_lock_raw_disclosed": True}


def main():
    out = {"schema": "issue8072-finite-v1", "seeds": SEEDS,
           "arms": [run_arm(s, a) for s in range(SEEDS) for a in ("FULL", "CONTROLLED")]}
    json.dump(out, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
