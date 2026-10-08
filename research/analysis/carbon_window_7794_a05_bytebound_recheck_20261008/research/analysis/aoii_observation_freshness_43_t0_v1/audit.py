#!/usr/bin/env python3
"""Independent literal-event replay auditor; does not import candidate.py."""
import json
import sys

EXPECTED_CASES = {"old_unchanged", "recent_superseded", "short_critical", "rapid_reversal", "missing_truth", "generation_change"}

def check(ok, message):
    if not ok:
        raise ValueError(message)

def audit(records):
    check(records[0]["type"] == "freeze" and records[0]["authority"] is False, "freeze/authority")
    trace = records[0]["trace"]
    check({e["case"] for e in trace} == EXPECTED_CASES, "case denominator")
    check(records[-1] == {"type": "source", "trace_sha256": records[0]["trace_sha256"], "deliveries_per_policy": 6}, "terminal source receipt")
    events = {}
    for event in trace:
        events.setdefault(event["case"], []).append(event)
    deliveries = [r for r in records if r.get("type") == "delivery"]
    check(len(deliveries) == 12, "delivery denominator")
    expected = []
    for case, rows in events.items():
        truths = sorted((r for r in rows if r["op"] == "truth"), key=lambda r: r["tick"])
        captures = {r["capture"]: r for r in rows if r["op"] == "capture"}
        check(len([r for r in rows if r["op"] == "deliver"]) == 2, "per-case matched policy denominator")
        for d in (r for r in rows if r["op"] == "deliver"):
            c = captures[d["capture"]]
            current = next((t for t in reversed(truths) if t["tick"] <= d["tick"]), None)
            known = current is not None
            gen_match = known and c["generation"] == current["generation"]
            expected.append((case, d["policy"], d["tick"] - c["tick"], d["belief"], None if not known else current["value"], known, gen_match, None if not known else d["belief"] != current["value"]))
    seen = set()
    for row in deliveries:
        check(row["authority"] is False, "authority mutation")
        actual = (row["case"], row["policy"], row["age"], row["belief"], row["truth"], row["known"], row["generation_match"], row["incorrect"])
        check(actual in expected, "independent replay mismatch")
        key = (row["case"], row["policy"])
        check(key not in seen, "duplicate delivery")
        seen.add(key)
    check(seen == {(c, p) for c in EXPECTED_CASES for p in ("LATEST_BY_CAPTURE_TIME", "COVERAGE_THEN_LATEST")}, "missing policy rows")
    old = [r for r in deliveries if r["case"] == "old_unchanged"]
    recent = [r for r in deliveries if r["case"] == "recent_superseded"]
    check(all(r["age"] == 5 and r["incorrect"] is False for r in old), "old-but-unchanged distinction")
    check(all(r["age"] == 1 and r["incorrect"] is True for r in recent), "fresh-but-wrong distinction")
    check(all(r["known"] is False and r["incorrect"] is None for r in deliveries if r["case"] == "missing_truth"), "UNKNOWN not zero-error")
    check(all(r["generation_match"] is False for r in deliveries if r["case"] == "generation_change"), "generation mismatch")
    reverse = [r for r in deliveries if r["case"] == "rapid_reversal"]
    check({r["incorrect"] for r in reverse} == {False, True}, "rapid reversal belief contrast")
    return {"rows": len(deliveries), "cases": len(EXPECTED_CASES), "old_aoi": old[0]["age"], "old_aoii": sum(r["incorrect"] is True for r in old), "fresh_wrong_aoi": recent[0]["age"], "fresh_wrong_aoii": sum(r["incorrect"] is True for r in recent), "rapid_reversal_aoii": sum(r["incorrect"] is True for r in reverse), "authority_grants": 0, "status": "PASS_METHOD_SCOPED"}

def main(path):
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    print(json.dumps(audit(rows), sort_keys=True))

if __name__ == "__main__":
    main(sys.argv[1])
