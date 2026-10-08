#!/usr/bin/env python3
"""Independent raw-only auditor for Issue #5709. Does not import runner."""
import json
import sys

EXPECTED = ["comfortable", "thin", "crossing", "safe_stop", "missing_time", "altered_opportunities"]
BASE = {"opp-01", "opp-02", "opp-03", "opp-04"}

def audit(rows):
    errors = []
    if [r.get("case") for r in rows] != EXPECTED:
        errors.append("case_order_or_count")
        return errors
    by = {r["case"]: r for r in rows}
    for name in ("comfortable", "thin", "crossing", "safe_stop", "missing_time"):
        if set(by[name].get("opportunity_ids", [])) != BASE:
            errors.append(name + ":opportunities")
    c, t = by["comfortable"], by["thin"]
    if c["policy_a"]["forbidden_effects"] != t["policy_a"]["forbidden_effects"] or c["crossings"] != t["crossings"]:
        errors.append("event_only_counts_differ")
    if c["opportunity_ids"] != t["opportunity_ids"]:
        errors.append("matched_ids_differ")
    if min(c["policy_a"]["margins_ms"]) == min(t["policy_a"]["margins_ms"]):
        errors.append("margin_ledger_did_not_distinguish")
    x = by["crossing"]
    if x["crossings"] != 1 or min(x["policy_a"]["margins_ms"]) >= 0 or x["disposition"] != "BOUNDARY_CROSSED":
        errors.append("crossing_not_reconstructed")
    s = by["safe_stop"]
    if s["stops"] != 1 or s["disposition"] != "STOP_RECORDED_OUTCOME_UNKNOWN":
        errors.append("safe_stop_overclaimed")
    m = by["missing_time"]
    if m["unknown"] != 1 or m["disposition"] != "UNKNOWN" or None not in m["policy_a"]["margins_ms"]:
        errors.append("missing_time_not_unknown")
    a = by["altered_opportunities"]
    if set(a["policy_a"]["opportunity_ids"]) == set(a["policy_b"]["opportunity_ids"]) or a["disposition"] != "HOLD_NO_STABLE_DENOMINATOR":
        errors.append("altered_opportunities_not_held")
    return errors

def main():
    raw = open(sys.argv[1], encoding="utf-8").read().splitlines()
    rows = [json.loads(line) for line in raw]
    errors = audit(rows)
    print(json.dumps({"rows": len(rows), "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD", "errors": errors}, sort_keys=True))
    raise SystemExit(bool(errors))

if __name__ == "__main__":
    main()
