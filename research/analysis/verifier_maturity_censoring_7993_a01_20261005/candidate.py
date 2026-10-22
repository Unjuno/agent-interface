#!/usr/bin/env python3
"""Candidate risk summaries; reads observation-only input, never oracle truth."""
from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path

PROTOCOL = "issue-7993-t0-a01-v1"
STATUSES = {"resolved", "pending", "safe_terminal_stop", "permanent_loss_unknown_cause"}


def summarize(snapshot: dict, alpha: Fraction) -> dict:
    rows = snapshot["rows"]
    if not rows or len({r["row_id"] for r in rows}) != len(rows):
        raise ValueError("empty cohort or duplicate row id")
    if any(r["status"] not in STATUSES for r in rows):
        raise ValueError("unknown observation status")
    if any((r["status"] == "resolved") != ("loss" in r) for r in rows):
        raise ValueError("loss must exist exactly for resolved labels")
    if any(r.get("loss") not in (0, 1) for r in rows if r["status"] == "resolved"):
        raise ValueError("loss must be binary")

    n = len(rows)
    resolved = [r for r in rows if r["status"] == "resolved"]
    unresolved = [r for r in rows if r["status"] != "resolved"]
    errors = sum(r["loss"] for r in resolved)
    cc_risk = Fraction(errors, len(resolved)) if resolved else None
    lower = Fraction(errors, n)
    upper = Fraction(errors + len(unresolved), n)
    counts = {status: sum(r["status"] == status for r in rows) for status in sorted(STATUSES)}

    model = snapshot["model"]
    adjustment_status = "ELIGIBLE"
    reason = "known verified outcome-independent follow-up with positive support"
    estimate = None
    if not model.get("known"):
        adjustment_status, reason = "UNKNOWN", "censor model not known"
    elif model.get("independence") != "verified":
        adjustment_status, reason = "UNKNOWN", "outcome-independence assumption not verified"
    elif any(r["status"] in {"safe_terminal_stop", "permanent_loss_unknown_cause"} for r in rows):
        adjustment_status, reason = "UNKNOWN", "typed terminal/loss status is not ordinary censoring"
    else:
        pis = model.get("pi_by_stratum", {})
        row_pis = [Fraction(pis.get(r["stratum"], "0")) for r in rows]
        if any(pi <= 0 or pi > 1 for pi in row_pis):
            adjustment_status, reason = "UNKNOWN", "zero/invalid follow-up probability violates positivity"
        else:
            # Horvitz–Thompson total divided by fixed assigned cohort size.
            estimate = sum((Fraction(r["loss"]) / Fraction(pis[r["stratum"]])
                            for r in resolved), Fraction(0, 1)) / n

    return {
        "snapshot_id": snapshot["snapshot_id"],
        "case_id": snapshot["case_id"],
        "checkpoint": snapshot["checkpoint"],
        "n_assigned": n,
        "status_counts": counts,
        "complete_case": {
            "risk": None if cc_risk is None else str(cc_risk),
            "naive_le_alpha": None if cc_risk is None else cc_risk <= alpha,
        },
        "all_assigned_bounds": {
            "lower": str(lower), "upper": str(upper),
            "supports_le_alpha": upper <= alpha,
        },
        "censor_adjusted": {
            "status": adjustment_status,
            "reason": reason,
            "estimator": "horvitz_thompson_point_estimate" if estimate is not None else None,
            "point_estimate": None if estimate is None else str(estimate),
            "is_risk_certificate": False,
        },
    }


def run(input_path: Path) -> dict:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    if data.get("protocol") != PROTOCOL or data.get("endpoint") != "verifier_claim_contradicted_by_final_oracle":
        raise ValueError("wrong protocol or endpoint")
    alpha = Fraction(data["alpha"])
    return {"protocol": PROTOCOL, "alpha": str(alpha),
            "records": [summarize(s, alpha) for s in data["snapshots"]]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("candidate_input.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.input)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"protocol": PROTOCOL, "snapshot_count": len(result["records"]),
                      "output": args.output.name}, sort_keys=True))


if __name__ == "__main__":
    main()
