#!/usr/bin/env python3
"""Deterministic obstacle/contradiction preflight for #2540.

Construction-only: no backend, GUI, input, model, network, or authority.
"""
from __future__ import annotations
import hashlib, json

MODES = (
    "CURRENT_AND_HISTORY_ONLY",
    "SPECULATIVE_WITH_TTL",
    "SPECULATION_WITH_FRESH_GUARD",
    "SPECULATION_UNMARKED",
)
CASES = (
    ("stable", "expected", "fresh"),
    ("obstacle_before_decision", "reversal", "fresh"),
    ("obstacle_before_effect", "reversal", "fresh"),
    ("target_replacement", "new_target", "fresh"),
    ("delayed_capture", "expected", "stale"),
    ("unavailable_fresh_evidence", "expected", "missing"),
    ("ambiguous_noisy_direction", "ambiguous", "fresh"),
    ("mislabeled_observed", "expected", "mislabeled"),
)

def decide(mode: str, state: str, freshness: str) -> dict:
    contradiction = state in {"reversal", "new_target", "ambiguous"} or freshness in {
        "stale", "missing", "mislabeled"
    }
    if mode == "CURRENT_AND_HISTORY_ONLY":
        outcome = "UNKNOWN_YIELD" if contradiction else "OBSERVED_NO_AUTHORITY"
    elif mode == "SPECULATION_WITH_FRESH_GUARD":
        outcome = "INVALIDATED_UNKNOWN_YIELD" if contradiction else "MATCHED_NO_AUTHORITY"
    elif mode == "SPECULATIVE_WITH_TTL":
        outcome = "EXPIRED_UNKNOWN_YIELD" if freshness in {"stale", "missing"} else (
            "PREDICTED_NO_AUTHORITY" if not contradiction else "STALE_RISK_UNKNOWN"
        )
    else:
        outcome = "UNMARKED_PREDICTION" if not contradiction else "UNMARKED_CONTRADICTION"
    return {
        "mode": mode,
        "state": state,
        "freshness": freshness,
        "outcome": outcome,
        "authority_granted": False,
        "input_executed": False,
    }

def oracle(row: dict) -> bool:
    contradiction = row["state"] in {"reversal", "new_target", "ambiguous"} or row["freshness"] in {
        "stale", "missing", "mislabeled"
    }
    if contradiction:
        return row["outcome"] in {
            "UNKNOWN_YIELD", "INVALIDATED_UNKNOWN_YIELD", "EXPIRED_UNKNOWN_YIELD",
            "STALE_RISK_UNKNOWN", "UNMARKED_CONTRADICTION",
        }
    return not row["authority_granted"] and not row["input_executed"]

def main() -> None:
    rows = []
    for case, state, freshness in CASES:
        for mode in MODES:
            row = {"case": case, **decide(mode, state, freshness)}
            row["oracle_pass"] = oracle(row)
            rows.append(row)
    summary = {
        "schema": "temporal-speculation-obstacle-preflight-v1",
        "formal": False,
        "cases": len(CASES),
        "modes": len(MODES),
        "rows": len(rows),
        "oracle_pass": sum(r["oracle_pass"] for r in rows),
        "authority_grants": sum(r["authority_granted"] for r in rows),
        "input_executions": sum(r["input_executed"] for r in rows),
        "contradiction_rows": sum(
            r["state"] in {"reversal", "new_target", "ambiguous"} or
            r["freshness"] in {"stale", "missing", "mislabeled"} for r in rows
        ),
        "rows_sha256": hashlib.sha256(
            json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "rows": rows,
    }
    print(json.dumps(summary, sort_keys=True))

if __name__ == "__main__":
    main()
