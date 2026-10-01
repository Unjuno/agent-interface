"""Deterministic, standard-library-only calibration fixture for Issue #1911."""
from __future__ import annotations

import hashlib
import json
import random
from fractions import Fraction
from pathlib import Path

N = 1000
SEED = 1911
HORIZON = 4
MIN_CENSORED_DWELL = HORIZON + 1
MAX_DWELL = {"A": 6, "B": 7}


def authored_rows() -> list[dict]:
    rows = []
    for state, next_state, dwell_values in (
        ("S0", "A", [2] * 200 + [4] * 200 + [6] * 200),
        ("S0", "B", [1] * 200 + [5] * 100 + [7] * 100),
    ):
        for dwell in dwell_values:
            rows.append({"state": state, "action": "GO", "next_state": next_state, "dwell": dwell})
    rng = random.Random(SEED)
    rng.shuffle(rows)
    return [{"episode_id": i, **row} for i, row in enumerate(rows)]


def visible_ledger(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        complete = row["dwell"] <= HORIZON
        out.append(
            {
                "episode_id": row["episode_id"],
                "state": row["state"],
                "action": row["action"],
                "next_state": row["next_state"],
                "state_signal_time": 0,
                "effect_status": "COMPLETE" if complete else "CENSORED",
                "effect_time_or_censor": row["dwell"] if complete else HORIZON,
                "horizon": HORIZON,
            }
        )
    return out


def digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def summarize(ledger: list[dict]) -> dict:
    by_state = {state: [r for r in ledger if r["next_state"] == state] for state in ("A", "B")}
    intervals = {}
    for state, rows in by_state.items():
        completed = [r["effect_time_or_censor"] for r in rows if r["effect_status"] == "COMPLETE"]
        censored = sum(r["effect_status"] == "CENSORED" for r in rows)
        # Right-censoring means dwell > HORIZON, so the sharp integer fixture
        # lower bound is the first unobserved value, HORIZON + 1.
        lower = Fraction(sum(completed) + censored * MIN_CENSORED_DWELL, len(rows))
        upper = Fraction(sum(completed) + censored * MAX_DWELL[state], len(rows))
        intervals[state] = {"lower": str(lower), "upper": str(upper), "complete": len(completed), "censored": censored}
    a_count = len(by_state["A"])
    completed_only_a = sum(r["next_state"] == "A" and r["effect_status"] == "COMPLETE" for r in ledger)
    completed_only_total = sum(r["effect_status"] == "COMPLETE" for r in ledger)
    return {"rows": len(ledger), "unique_ids": len({r["episode_id"] for r in ledger}), "counts": {"A": a_count, "B": len(by_state["B"])}, "p_A": str(Fraction(a_count, len(ledger))), "intervals": intervals, "authored_mean": {"A": "4", "B": "7/2"}, "completion_only_p_A": str(Fraction(completed_only_a, completed_only_total))}


def audit(rows: list[dict], ledger: list[dict], summary: dict) -> dict:
    expected = {"A": 600, "B": 400}
    errors = []
    if len(rows) != N or len(ledger) != N or summary["unique_ids"] != N:
        errors.append("row_identity")
    if summary["counts"] != expected or summary["p_A"] != "3/5":
        errors.append("transition_population")
    if summary["intervals"] != {"A": {"lower": "11/3", "upper": "4", "complete": 400, "censored": 200}, "B": {"lower": "3", "upper": "4", "complete": 200, "censored": 200}}:
        errors.append("dwell_intervals")
    if summary["completion_only_p_A"] != "2/3":
        errors.append("censor_bias_comparator")
    return {"passed": not errors, "errors": errors, "ledger_sha256": digest(ledger), "summary": summary}


def main() -> int:
    rows = authored_rows()
    ledger = visible_ledger(rows)
    summary = summarize(ledger)
    result = audit(rows, ledger, summary)
    result["source"] = {"seed": SEED, "episodes": N, "horizon": HORIZON, "max_dwell": MAX_DWELL}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
