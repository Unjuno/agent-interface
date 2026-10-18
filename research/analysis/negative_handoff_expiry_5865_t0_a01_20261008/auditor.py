#!/usr/bin/env python3
"""Independent raw-only reconstruction for the frozen finite receipt table."""
import copy
import json
import sys


def independent_trace(case, receiver_renews):
    receipt = case["receipt"]
    kind = receipt.get("kind")
    if kind != "NO_MATCH":
        result = kind if kind in ("TIMEOUT", "ERROR") else "UNKNOWN"
        return [{"receiver": h["receiver"], "at": h["at"], "decision": result}
                for h in case["handoffs"]]
    if (receipt.get("clock_trusted") is not True or
            type(receipt.get("source_evaluation_at")) not in (int, float) or
            type(receipt.get("source_expiry")) not in (int, float) or
            receipt["source_expiry"] <= receipt["source_evaluation_at"] or
            receipt.get("source_epoch") != case["current_epoch"] or
            receipt.get("query") != case["query"] or
            receipt.get("scope") != case["scope"]):
        return [{"receiver": h["receiver"], "at": h["at"], "decision": "UNKNOWN"}
                for h in case["handoffs"]]
    result = []
    for handoff in case["handoffs"]:
        moment = handoff["at"]
        deadline = moment + receipt["ttl"] if receiver_renews else receipt["source_expiry"]
        answer = "NO_MATCH" if moment < deadline else "EXPIRED"
        result.append({"receiver": handoff["receiver"], "at": moment, "decision": answer})
    return result


def reconstruct(source):
    rows = []
    for case in source["cases"]:
        absolute_trace = independent_trace(case, False)
        sliding_trace = independent_trace(case, True)
        rows.append({"case_id": case["case_id"],
                     "absolute_trace": absolute_trace,
                     "sliding_trace": sliding_trace,
                     "absolute": absolute_trace[-1]["decision"],
                     "sliding": sliding_trace[-1]["decision"],
                     "authority": False})
    return rows


def audit(source, raw, expected):
    rebuilt = reconstruct(source)
    by_id = {row["case_id"]: row for row in rebuilt}
    errors = []
    if raw.get("schema") != "negative-handoff-expiry-raw-v1":
        errors.append("schema")
    if raw.get("rows") != rebuilt:
        errors.append("raw_reconstruction")
    if set(by_id) != set(expected["expected"]):
        errors.append("denominator")
    for cid, dispositions in expected["expected"].items():
        if cid not in by_id:
            errors.append("missing:" + cid)
            continue
        for arm, value in dispositions.items():
            if by_id[cid][arm] != value:
                errors.append("expected:" + cid + ":" + arm)
    if any(row["authority"] is not False for row in rebuilt):
        errors.append("authority")
    # Effective corruption challenges: each changes one source/result fact.
    rejected = {}
    for field in expected["mutation_fields"]:
        damaged_raw = copy.deepcopy(raw)
        index = {"now": 1, "source_expiry": 1, "source_epoch": 4,
                 "scope": 5, "kind": 7, "query": 8}[field]
        row = damaged_raw["rows"][index]
        if field == "now":
            row["sliding_trace"][-1]["at"] = 10.0
        elif field == "source_expiry":
            row["absolute"] = "NO_MATCH"
            row["absolute_trace"][-1]["decision"] = "NO_MATCH"
        elif field == "source_epoch":
            row["absolute"] = "NO_MATCH"
            row["absolute_trace"][-1]["decision"] = "NO_MATCH"
        elif field == "scope":
            row["absolute"] = "NO_MATCH"
            row["absolute_trace"][-1]["decision"] = "NO_MATCH"
        elif field == "query":
            row["absolute"] = "NO_MATCH"
            row["absolute_trace"][-1]["decision"] = "NO_MATCH"
        else:
            row["absolute"] = "NO_MATCH"
            row["absolute_trace"][-1]["decision"] = "NO_MATCH"
        rejected[field] = damaged_raw.get("rows") != rebuilt
    if not all(rejected.values()):
        errors.append("mutation_controls")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
            "rows": len(rebuilt), "errors": errors,
            "mutations_rejected": rejected,
            "late_sliding_false_acceptance": by_id.get("C02", {}).get("sliding") == "NO_MATCH" and by_id.get("C02", {}).get("absolute") == "EXPIRED"}


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        source = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        raw = json.load(f)
    with open(sys.argv[3], encoding="utf-8") as f:
        expected = json.load(f)
    result = audit(source, raw, expected)
    with open(sys.argv[4], "w", encoding="utf-8") as f:
        json.dump(result, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)
