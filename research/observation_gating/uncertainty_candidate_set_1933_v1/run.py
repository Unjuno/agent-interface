from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

from fixture import generate_cases
from policy import exact_max_set, top1_hard

DECISION_PASS = "PASS_AMBIGUITY_PRESERVING_CUE_SET_SCOPED"
DECISION_FAIL = "FAIL_AMBIGUITY_PRESERVING_CUE_SET"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ns = ap.parse_args()
    out = Path(ns.out)
    if out.exists():
        raise SystemExit("refuse_existing_output")
    out.mkdir(parents=True)

    rows = []
    for index, case in enumerate(generate_cases()):
        top1 = top1_hard(case.regions_before_b64, case.regions_after_b64)
        candidate = exact_max_set(case.regions_before_b64, case.regions_after_b64)
        rows.append({
            "index": index,
            "case_id": case.case_id,
            "family": case.family,
            "variant": case.variant,
            "true_region": case.true_region,
            "before_b64": list(case.regions_before_b64),
            "after_b64": list(case.regions_after_b64),
            "top1_hard": top1,
            "exact_max_set": candidate,
        })

    raw_obj = {
        "allocation_id": "uncertainty-candidate-set-1933-20260922-formal-01",
        "formal_invocations": 1,
        "reruns": 0,
        "replacements": 0,
        "tuning": 0,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "executable": sys.executable,
        },
        "rows": rows,
    }
    raw_bytes = (json.dumps(raw_obj, indent=2, sort_keys=True) + "\n").encode()
    (out / "RAW.json").write_bytes(raw_bytes)

    unique = [r for r in rows if r["family"] == "UNIQUE_TRUE"]
    ties = [r for r in rows if r["family"] != "UNIQUE_TRUE"]
    top1_tie_misses = sum(r["true_region"] not in r["top1_hard"]["selected_regions"] for r in ties)
    candidate_misses = sum(r["true_region"] not in r["exact_max_set"]["selected_regions"] for r in rows)
    candidate_nonmax = 0
    for r in rows:
        scores = r["exact_max_set"]["scores"]
        mx = max(scores)
        candidate_nonmax += sum(scores[i] != mx for i in r["exact_max_set"]["selected_regions"])
    unique_singleton_ok = sum(
        r["exact_max_set"]["selected_regions"] == [r["true_region"]]
        and r["exact_max_set"]["exclusive"] is True
        for r in unique
    )
    tie_cardinality_ok = sum(
        len(r["exact_max_set"]["selected_regions"]) == (2 if r["family"] == "TWO_WAY_TIE" else 3)
        and r["exact_max_set"]["exclusive"] is False
        for r in ties
    )
    authority_true = sum(
        bool(r[arm]["grants_input_authority"])
        for r in rows for arm in ("top1_hard", "exact_max_set")
    )

    gates = {
        "rows_48": len(rows) == 48,
        "unique_singleton_12": unique_singleton_ok == 12,
        "tie_cardinality_36": tie_cardinality_ok == 36,
        "candidate_misses_0": candidate_misses == 0,
        "candidate_nonmax_0": candidate_nonmax == 0,
        "top1_tie_misses_21": top1_tie_misses == 21,
        "authority_true_0": authority_true == 0,
    }
    decision = DECISION_PASS if all(gates.values()) else DECISION_FAIL
    result = {
        "decision": decision,
        "gates": gates,
        "counts": {
            "rows": len(rows),
            "unique": len(unique),
            "ties": len(ties),
            "top1_tie_misses": top1_tie_misses,
            "candidate_misses": candidate_misses,
            "candidate_nonmax": candidate_nonmax,
            "unique_singleton_ok": unique_singleton_ok,
            "tie_cardinality_ok": tie_cardinality_ok,
            "authority_true": authority_true,
        },
        "raw_sha256": sha256_bytes(raw_bytes),
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if decision == DECISION_PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
