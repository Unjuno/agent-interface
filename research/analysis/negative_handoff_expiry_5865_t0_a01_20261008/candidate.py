#!/usr/bin/env python3
"""Finite candidate: compare receiver-renewed TTL with source-time expiry."""
import json
import sys


def trace(case, sliding):
    receipt = case["receipt"]
    if receipt.get("kind") != "NO_MATCH":
        return [{"receiver": hop["receiver"], "at": hop["at"],
                 "decision": receipt.get("kind", "UNKNOWN")} for hop in case["handoffs"]]
    if (receipt.get("clock_trusted") is not True or
            type(receipt.get("source_evaluation_at")) not in (int, float) or
            type(receipt.get("source_expiry")) not in (int, float) or
            receipt["source_expiry"] <= receipt["source_evaluation_at"] or
            receipt.get("source_epoch") != case["current_epoch"] or
            receipt.get("query") != case["query"] or
            receipt.get("scope") != case["scope"]):
        return [{"receiver": hop["receiver"], "at": hop["at"],
                 "decision": "UNKNOWN"} for hop in case["handoffs"]]
    deadline = receipt["source_expiry"]
    timeline = []
    for hop in case["handoffs"]:
        at = hop["at"]
        decision = "NO_MATCH" if at < (at + receipt["ttl"] if sliding else deadline) else "EXPIRED"
        timeline.append({"receiver": hop["receiver"], "at": at, "decision": decision})
    return timeline


def run(data):
    result = []
    for case in data["cases"]:
        a = trace(case, False)
        s = trace(case, True)
        result.append({"case_id": case["case_id"],
                       "absolute_trace": a, "sliding_trace": s,
                       "absolute": a[-1]["decision"],
                       "sliding": s[-1]["decision"],
                       "authority": False})
    return {"schema": "negative-handoff-expiry-raw-v1", "rows": result}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        source = json.load(f)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(run(source), f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
