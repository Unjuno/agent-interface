#!/usr/bin/env python3
"""Independent raw-only audit; intentionally does not import candidate.py."""

from __future__ import annotations

import json
import itertools
import sys
from fractions import Fraction
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def audit(ledger: dict, raw: dict) -> dict:
    rows = ledger["episodes"]
    row_ids = [row.get("episode_id") for row in rows]
    require(all(isinstance(eid, str) and eid for eid in row_ids), "invalid row identity")
    require(len(row_ids) == len(set(row_ids)), "duplicate row identity")
    states = [row.get("outcome") for row in rows]
    require(set(states) <= {"SUCCESS", "FAIL", "UNRESOLVED"}, "unknown outcome")
    n = len(states)
    success = states.count("SUCCESS")
    failure = states.count("FAIL")
    missing = states.count("UNRESOLVED")
    require(n == success + failure + missing, "N != S + F + M")

    threshold_obj = ledger["promotion_threshold"]
    require(type(threshold_obj.get("numerator")) is int and
            type(threshold_obj.get("denominator")) is int and
            threshold_obj["denominator"] > 0, "invalid threshold encoding")
    tau = Fraction(threshold_obj["numerator"], threshold_obj["denominator"])
    lo, hi = Fraction(success, n), Fraction(success + missing, n)
    observed = Fraction(success, success + failure) if success + failure else None

    require(raw.get("schema") == "issue-5590-missing-outcome-bounds-result-v1", "schema mismatch")
    require(raw.get("cohort_id") == ledger.get("cohort_id"), "cohort mismatch")
    require(type(raw.get("denominator")) is int and raw["denominator"] == n,
            "denominator mismatch")
    require(raw.get("counts") == {"success": success, "failure": failure,
                                   "unresolved": missing}, "count mismatch")
    require(raw.get("threshold") == {"numerator": tau.numerator,
                                      "denominator": tau.denominator}, "threshold mismatch")
    expected_observed = None if observed is None else {
        "numerator": observed.numerator, "denominator": observed.denominator,
        "decision": "PROMOTE" if observed >= tau else "DO_NOT_PROMOTE",
    }
    require(raw.get("observed_only") == expected_observed, "observed-only result mismatch")
    expected_low = {"numerator": lo.numerator, "denominator": lo.denominator,
                    "decision": "PROMOTE" if lo >= tau else "DO_NOT_PROMOTE"}
    require(raw.get("missing_as_failure") == expected_low, "lower-bound result mismatch")
    expected_decision = ("PROMOTION_SUPPORTED" if lo >= tau else
                         "PROMOTION_REJECTED" if hi < tau else
                         "PROMOTION_UNIDENTIFIED")
    expected_bounds = {
        "lower": {"numerator": lo.numerator, "denominator": lo.denominator},
        "upper": {"numerator": hi.numerator, "denominator": hi.denominator},
        "decision": expected_decision,
    }
    require(raw.get("sharp_bounds") == expected_bounds, "bounds or decision mismatch")

    completions = raw.get("compatible_completions")
    require(type(completions) is list and len(completions) == 2 ** missing,
            "completion cardinality mismatch")
    unresolved_ids = [row["episode_id"] for row in rows if row["outcome"] == "UNRESOLVED"]
    expected_masks = {
        frozenset(group)
        for size in range(len(unresolved_ids) + 1)
        for group in itertools.combinations(unresolved_ids, size)
    }
    observed_masks = set()
    values = []
    for item in completions:
        chosen = item.get("unresolved_success_ids")
        require(type(chosen) is list and all(isinstance(eid, str) for eid in chosen),
                "invalid completion identity list")
        mask = frozenset(chosen)
        require(len(mask) == len(chosen) and mask <= set(unresolved_ids),
                "completion references duplicate or non-unresolved identity")
        require(mask not in observed_masks, "duplicate compatible completion")
        observed_masks.add(mask)
        k = item.get("success_count")
        require(type(k) is int and k == success + len(mask),
                "completion outside feasible success counts")
        rate = Fraction(k, n)
        require(item.get("rate") == {"numerator": rate.numerator,
                                      "denominator": rate.denominator}, "completion rate mismatch")
        require(item.get("decision") == ("PROMOTE" if rate >= tau else "DO_NOT_PROMOTE"),
                "completion decision mismatch")
        values.append(rate)
    require(observed_masks == expected_masks, "compatible completion set mismatch")
    require(min(values) == lo and max(values) == hi, "bounds are not sharp over completions")
    require(raw.get("completion_count") == len(completions), "completion count mismatch")
    return {"status": "PASS_BOUNDS_SCOPED", "errors": [], "N": n,
            "S": success, "F": failure, "M": missing,
            "lower": str(lo), "upper": str(hi), "completion_count": len(completions)}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: audit.py LEDGER.json RAW.json", file=sys.stderr)
        return 2
    try:
        ledger = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        raw = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        result = audit(ledger, raw)
    except Exception as exc:
        print(json.dumps({"status": "FAIL_INTEGRITY", "errors": [str(exc)]}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
