#!/usr/bin/env python3
"""Post-run raw-ledger integrity revalidation; does not replace frozen audit."""
import copy
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "formal_01"
DOSES = tuple(range(0, 25, 2))
LOCATIONS = (("PLANNER_BOUNDARY", 0), ("LOCAL_PROCESSING", 4))


def expected_rows():
    rng = random.Random(7411001)
    thresholds = [6 + (person % 9) for person in range(160)]
    rng.shuffle(thresholds)
    rows = []
    for person, base in enumerate(thresholds):
        for location, offset in LOCATIONS:
            threshold = base + offset
            for dose in DOSES:
                missing = rng.random() < 0.02
                tie = (not missing) and rng.random() < 0.08
                probability = 1.0 / (1.0 + math.exp(-(dose - threshold) / 1.5))
                if rng.random() < 0.04:
                    probability = 0.5
                if missing:
                    choice = "MISSING"
                elif tie:
                    choice = "TIE"
                else:
                    choice = "FASTER" if rng.random() < probability else "SAME"
                rows.append({"respondent": person, "location": location, "dose_seconds": dose,
                             "choice": choice, "task_effect_equal": True, "safety_gate": "PASS"})
    return rows


def validate_raw(raw):
    if raw.get("schema") != "issue-7411-t0-a01-raw-v1" or raw.get("seed") != 7411001:
        raise ValueError("schema_or_seed")
    if raw.get("doses_seconds") != list(DOSES):
        raise ValueError("dose_vector")
    if raw.get("rows") != expected_rows():
        raise ValueError("rows_not_exact_frozen_generation")
    if len({(r["respondent"], r["location"], r["dose_seconds"]) for r in raw["rows"]}) != 4160:
        raise ValueError("duplicate_or_missing_cell")
    low = raw.get("low_support_rows", [])
    expected_low = [{"respondent": i, "location": "LOW_SUPPORT", "dose_seconds": dose,
                     "choice": "SAME", "task_effect_equal": True, "safety_gate": "PASS"}
                    for i in range(20) for dose in (0, 2, 4, 6)]
    if low != expected_low:
        raise ValueError("low_support_rows")
    gate = raw.get("correctness_regression_control", {})
    if gate != {"mean_preference_faster": 0.9, "task_effect_equal": False,
                "safety_gate": "FAIL", "adoption_eligible": False}:
        raise ValueError("hard_gate_control")


def estimate(rows):
    # Independent grouped cumulative proportions and monotone pool-adjacent-violators fit.
    groups = []
    for dose in DOSES:
        answered = [row["choice"] for row in rows if row["dose_seconds"] == dose and row["choice"] in ("FASTER", "SAME")]
        groups.append([dose, sum(v == "FASTER" for v in answered), len(answered)])
    pool = []
    for dose, yes, n in groups:
        pool.append([dose, dose, yes, n])
        while len(pool) > 1:
            left, right = pool[-2:]
            pleft = left[2] / left[3] if left[3] else 0.0
            pright = right[2] / right[3] if right[3] else 0.0
            if pleft <= pright:
                break
            pool[-2:] = [[left[0], right[1], left[2] + right[2], left[3] + right[3]]]
    pool = [item for item in pool if item[3]]
    if not pool or pool[0][2] / pool[0][3] >= .5 or pool[-1][2] / pool[-1][3] < .5:
        return {"status": "UNKNOWN", "threshold_seconds": None, "support": len(pool)}
    high = next(item for item in pool if item[2] / item[3] >= .5)
    lower = [item for item in pool if item[1] < high[0]]
    if not lower:
        return {"status": "UNKNOWN", "threshold_seconds": None, "support": len(pool)}
    return {"status": "ESTIMATED", "threshold_seconds": (max(lower, key=lambda x: x[1])[1] + high[0]) / 2,
            "support": len(pool)}


def must_reject(mutant):
    try:
        validate_raw(mutant)
    except (ValueError, KeyError, TypeError):
        return True
    return False


def main():
    raw_bytes = (OUT / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    candidate = json.loads((OUT / "candidate.json").read_text())
    validate_raw(raw)
    estimates = {location: estimate([row for row in raw["rows"] if row["location"] == location])
                 for location, _ in LOCATIONS}
    expected_truth = {"PLANNER_BOUNDARY": 10, "LOCAL_PROCESSING": 14}
    if estimates != candidate["estimates"]:
        raise SystemExit("posthoc estimator reconstruction differs from candidate")
    if any(abs(estimates[key]["threshold_seconds"] - value) > 2 for key, value in expected_truth.items()):
        raise SystemExit("posthoc threshold gate failed")
    if estimate(raw["low_support_rows"])["status"] != "UNKNOWN":
        raise SystemExit("low-support abstention failed")
    mutations = []
    for field, value in (("dose_seconds", 1), ("location", "UNKNOWN_ACTOR"), ("choice", "FABRICATED")):
        changed = copy.deepcopy(raw)
        changed["rows"][0][field] = value
        mutations.append(must_reject(changed))
    changed = copy.deepcopy(raw)
    changed["correctness_regression_control"]["adoption_eligible"] = True
    mutations.append(must_reject(changed))
    result = {"schema": "issue-7411-t0-a01-posthoc-audit-v1", "status": "POSTHOC_RAW_REVALIDATION_PASS",
              "formal_gate_replaced": False, "formal_disposition_remains": "HOLD_AUDIT_INCOMPLETE",
              "rows_exactly_regenerated": len(raw["rows"]), "estimates_recomputed": estimates,
              "low_support": estimate(raw["low_support_rows"]), "effective_mutations_rejected": sum(mutations),
              "mutations_total": len(mutations), "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "scope": "Post-run consistency check of synthetic records only; not preregistered formal evidence."}
    if mutations != [True] * 4:
        result["status"] = "POSTHOC_REVALIDATION_FAIL"
        (ROOT / "post_run_review.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        raise SystemExit("one or more effective mutations were not rejected")
    (ROOT / "post_run_review.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
