"""Independent, mutation-oriented audit for the #1911 fixture result."""
from __future__ import annotations

import copy
import json
from fractions import Fraction

from experiment import HORIZON, MAX_DWELL, authored_rows, visible_ledger


def independent_summary(ledger: list[dict]) -> dict:
    counts = {s: sum(row["next_state"] == s for row in ledger) for s in ("A", "B")}
    intervals = {}
    for state in ("A", "B"):
        rows = [r for r in ledger if r["next_state"] == state]
        complete = [r["effect_time_or_censor"] for r in rows if r["effect_status"] == "COMPLETE"]
        censored = [r for r in rows if r["effect_status"] == "CENSORED"]
        lower = Fraction(sum(complete) + len(censored) * (HORIZON + 1), len(rows))
        upper = Fraction(sum(complete) + len(censored) * MAX_DWELL[state], len(rows))
        intervals[state] = (str(lower), str(upper), len(complete), len(censored))
    return {"counts": counts, "intervals": intervals, "ids": len({r["episode_id"] for r in ledger})}


def valid(ledger: list[dict]) -> bool:
    summary = independent_summary(ledger)
    return (
        len(ledger) == 1000
        and summary["ids"] == 1000
        and {row["episode_id"] for row in ledger} == set(range(1000))
        and summary["counts"] == {"A": 600, "B": 400}
        and summary["intervals"] == {"A": ("11/3", "4", 400, 200), "B": ("3", "4", 200, 200)}
        and all(row["state"] == "S0" and row["action"] == "GO" and row["horizon"] == HORIZON for row in ledger)
    )


def main() -> int:
    ledger = visible_ledger(authored_rows())
    mutations = []
    for field, value in (("next_state", "B"), ("effect_status", "COMPLETE"), ("horizon", 5), ("episode_id", 1001)):
        mutated = copy.deepcopy(ledger)
        mutated[0][field] = value
        mutations.append(not valid(mutated))
    result = {"passed": valid(ledger) and all(mutations), "clean_pass": valid(ledger), "corruption_controls": mutations, "audit": independent_summary(ledger)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
