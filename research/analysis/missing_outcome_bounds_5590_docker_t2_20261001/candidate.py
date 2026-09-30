#!/usr/bin/env python3
"""Candidate computation for the frozen synthetic #5590 finite cohort."""

from __future__ import annotations

import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path


def classify(value: Fraction, threshold: Fraction) -> str:
    if value >= threshold:
        return "PROMOTE"
    return "DO_NOT_PROMOTE"


def compute(ledger: dict) -> dict:
    episodes = ledger["episodes"]
    ids = [row["episode_id"] for row in episodes]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate episode identity")
    if any(row["outcome"] not in {"SUCCESS", "FAIL", "UNRESOLVED"} for row in episodes):
        raise ValueError("invalid outcome state")
    n = len(episodes)
    counts = {state: sum(row["outcome"] == state for row in episodes)
              for state in ("SUCCESS", "FAIL", "UNRESOLVED")}
    if n != sum(counts.values()):
        raise ValueError("denominator does not reconcile")

    s, f, m = counts["SUCCESS"], counts["FAIL"], counts["UNRESOLVED"]
    threshold = Fraction(ledger["promotion_threshold"]["numerator"],
                         ledger["promotion_threshold"]["denominator"])
    observed = Fraction(s, s + f) if s + f else None
    lower, upper = Fraction(s, n), Fraction(s + m, n)
    if lower >= threshold:
        interval_decision = "PROMOTION_SUPPORTED"
    elif upper < threshold:
        interval_decision = "PROMOTION_REJECTED"
    else:
        interval_decision = "PROMOTION_UNIDENTIFIED"

    completions = []
    unresolved_ids = [row["episode_id"] for row in episodes
                      if row["outcome"] == "UNRESOLVED"]
    for bits in itertools.product((0, 1), repeat=m):
        resolved_successes = s + sum(bits)
        rate = Fraction(resolved_successes, n)
        completions.append({
            "unresolved_success_ids": [eid for eid, bit in zip(unresolved_ids, bits) if bit],
            "success_count": resolved_successes,
            "rate": {"numerator": rate.numerator, "denominator": rate.denominator},
            "decision": classify(rate, threshold),
        })

    return {
        "schema": "issue-5590-missing-outcome-bounds-result-v1",
        "cohort_id": ledger["cohort_id"],
        "denominator": n,
        "counts": {"success": s, "failure": f, "unresolved": m},
        "threshold": {"numerator": threshold.numerator,
                      "denominator": threshold.denominator},
        "observed_only": None if observed is None else {
            "numerator": observed.numerator, "denominator": observed.denominator,
            "decision": classify(observed, threshold),
        },
        "missing_as_failure": {"numerator": lower.numerator,
                               "denominator": lower.denominator,
                               "decision": classify(lower, threshold)},
        "sharp_bounds": {
            "lower": {"numerator": lower.numerator, "denominator": lower.denominator},
            "upper": {"numerator": upper.numerator, "denominator": upper.denominator},
            "decision": interval_decision,
        },
        "completion_count": len(completions),
        "compatible_completions": completions,
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: candidate.py LEDGER.json OUTPUT.json", file=sys.stderr)
        return 2
    ledger_path, output_path = map(Path, sys.argv[1:])
    result = compute(json.loads(ledger_path.read_text(encoding="utf-8")))
    Path(output_path).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                                 encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "output": str(output_path),
                      "completion_count": result["completion_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
