#!/usr/bin/env python3
"""Independent raw-only reconstruction for Issue #8072 T0."""
import json
import random
import copy
import statistics
import sys

ROUNDS = 8
GATE = 2
DEV_SIZE = 16


def reconstruct_cohorts(seed):
    cohorts = []
    for size, salt in ((DEV_SIZE, 1), (128, 2)):
        rng = random.Random(seed * 1009 + salt)
        rows = []
        for i in range(size):
            stratum, truth = rng.randrange(4), rng.randrange(2)
            rows.append({"id": f"{salt}:{i}", "stratum": stratum, "truth": truth,
                         "baseline": truth if i % 2 == 0 else 1-truth})
        cohorts.append(rows)
    return cohorts


def count_correct(rows, patched, transferred):
    total = 0
    for task in rows:
        prediction = task["truth"] if (task["id"] in patched or task["stratum"] in transferred) else task["baseline"]
        total += int(prediction == task["truth"])
    return total


def audit(raw):
    errors, optimism, utility = [], {"FULL": [], "CONTROLLED": []}, {"FULL": [], "CONTROLLED": []}
    if raw.get("schema") != "issue8072-finite-v1" or len(raw.get("arms", [])) != 200:
        errors.append("shape")
    for result in raw.get("arms", []):
        seed, arm = result.get("seed"), result.get("arm")
        dev, fresh = reconstruct_cohorts(seed)
        if arm not in optimism or len(result.get("queries", [])) != ROUNDS:
            errors.append(f"arm/queries:{seed}"); continue
        p, st = set(), set()
        for q, row in enumerate(result["queries"]):
            prop = row["proposal"]
            if arm == "FULL":
                first = next((r for r in dev if count_correct([r], p, st) == 0), None)
                expected = {"kind": "PATCH_ID", "target": first["id"] if first else None}
            else:
                expected = {"kind": "TRANSFER_STRATUM", "target": q % 4}
            current = count_correct(dev, p, st)
            tp, ts = set(p), set(st)
            if expected["kind"] == "PATCH_ID" and expected["target"] is not None: tp.add(expected["target"])
            if expected["kind"] == "TRANSFER_STRATUM": ts.add(expected["target"])
            proposed = count_correct(dev, tp, ts)
            veto = q == 6
            accepted = not veto and (proposed-current >= GATE if arm == "CONTROLLED" else proposed > current)
            if (prop != expected or row.get("before") != current or row.get("proposed") != proposed
                or row.get("hard_failure") != veto or row.get("veto") != veto
                or row.get("exact_safety_disclosed") is not True or row.get("accepted") != accepted
                or row.get("fresh_read") is not False): errors.append(f"query:{seed}:{arm}:{q}")
            if accepted: p, st = tp, ts
        dc, fc = count_correct(dev, p, st), count_correct(fresh, p, st)
        if (result.get("dev_correct"), result.get("fresh_correct"), result.get("locked_before_fresh"),
            result.get("post_lock_raw_disclosed")) != (dc, fc, True, True): errors.append(f"final:{seed}:{arm}")
        optimism[arm].append(dc/len(dev)-fc/len(fresh)); utility[arm].append(fc/len(fresh))
    med = {a: statistics.median(v) for a, v in optimism.items()}
    mean = {a: sum(v)/len(v) for a, v in utility.items()}
    decision = ("PASS_METHOD_SCOPED" if not errors and med["CONTROLLED"] < med["FULL"]
                and mean["CONTROLLED"] >= mean["FULL"]-0.05 else "FAIL_METHOD")
    return {"decision": decision, "errors": errors, "median_optimism": med,
            "mean_fresh_utility": mean, "seed_count": len(utility["FULL"]),
            "claim_scope": "authored finite synthetic mechanism only"}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f: raw = json.load(f)
    json.dump(audit(raw), sys.stdout, sort_keys=True, indent=2); print()
