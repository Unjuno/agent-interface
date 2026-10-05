#!/usr/bin/env python3
"""Candidate sees only empirical diagnostic counts and the frozen gate."""
import json


def execute(data):
    rows = []
    for row in data["rows"]:
        rates = [x / row["n"] for x in row["successes"]]
        peak_index = max(range(len(rates)), key=lambda i: (rates[i], -i))
        eligible = max(rates) - min(rates) >= data["minimum_span"] and max(rates) >= data["minimum_peak"]
        rows.append({"row_id": row["row_id"], "eligible": eligible,
                     "top_pair": data["pair_order"][peak_index], "rates": rates})
    return {"schema": "issue8084-a03-candidate-v1", "rows": rows}


if __name__ == "__main__":
    with open("observed_counts.json", encoding="utf-8") as f:
        result = execute(json.load(f))
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
