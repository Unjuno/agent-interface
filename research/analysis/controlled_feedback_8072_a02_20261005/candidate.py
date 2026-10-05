#!/usr/bin/env python3
"""Deterministic finite simulation for Issue #8072; standard library only."""
import json
import random
import sys

SEEDS, DEV_N, FRESH_N, QUERIES, THRESHOLD_ROWS = 100, 16, 128, 8, 2


def cohort(seed, n, salt):
    rng = random.Random(seed * 1009 + salt)
    rows = []
    for i in range(n):
        truth = rng.randrange(2)
        rows.append({"id": f"{salt}:{i}", "stratum": rng.randrange(4),
                     "truth": truth, "baseline": truth if i % 2 == 0 else 1-truth})
    return rows


def build(seed):
    return cohort(seed, DEV_N, 1), cohort(seed, FRESH_N, 2)


def score(rows, patches, strata):
    return sum(row["truth"] == (row["truth"] if row["id"] in patches or row["stratum"] in strata else row["baseline"])
               for row in rows)


def run_arm(seed, arm):
    dev, fresh = build(seed)
    patches, strata, queries = set(), set(), []
    for q in range(QUERIES):
        current = score(dev, patches, strata)
        if arm == "FULL":
            first = next((r for r in dev if score([r], patches, strata) == 0), None)
            proposal = {"kind": "PATCH_ID", "target": first["id"] if first else None}
        else:
            proposal = {"kind": "TRANSFER_STRATUM", "target": q % 4}
        tp, ts = set(patches), set(strata)
        if proposal["kind"] == "PATCH_ID" and proposal["target"] is not None: tp.add(proposal["target"])
        if proposal["kind"] == "TRANSFER_STRATUM": ts.add(proposal["target"])
        proposed = score(dev, tp, ts)
        hard_failure = q == 6
        feedback = ({"utility_rows": proposed-current} if arm == "FULL" else
                    {"accepted_threshold": proposed-current >= THRESHOLD_ROWS})
        veto = hard_failure
        accept = not veto and (proposed > current if arm == "FULL" else proposed-current >= THRESHOLD_ROWS)
        if accept: patches, strata = tp, ts
        queries.append({"q": q, "proposal": proposal, "before": current, "proposed": proposed,
                        "hard_failure": hard_failure, "exact_safety_disclosed": True, "veto": veto,
                        "feedback": feedback, "accepted": accept, "fresh_read": False})
    return {"seed": seed, "arm": arm, "queries": queries, "locked_before_fresh": True,
            "dev_correct": score(dev, patches, strata), "dev_n": len(dev),
            "fresh_correct": score(fresh, patches, strata), "fresh_n": len(fresh),
            "patches": sorted(patches), "strata": sorted(strata), "post_lock_raw_disclosed": True}


if __name__ == "__main__":
    result = {"schema": "issue8072-finite-a02-v1", "seeds": SEEDS,
              "arms": [run_arm(s, a) for s in range(SEEDS) for a in ("FULL", "CONTROLLED")]}
    json.dump(result, sys.stdout, sort_keys=True, separators=(",", ":")); print()
