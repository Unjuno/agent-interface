"""Independent comparison of held-input replay rows to the prior T0 table."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from statistics import median


EXPECTED_INPUT_SHA256 = {
    "candidate_v38.json": "55771151887660b4a264d9e788410e12e2e6e45ca4f4c9d96db1a5f93e85e5f1",
    "candidate_v39.json": "49a47182f6d6f3fdb944224882be5716a0452b2cc88beee51b482ef915be5fc0",
    "prior_audited_intervals.json": "2aab450e687cce4b912a83d548b9ab76165ed1826110e7506468efe2891ef7df",
}
DISPLAY_TOLERANCE_MS = 0.000500001
AGGREGATE_TOLERANCE = 1e-9


def near(a, b, tolerance=AGGREGATE_TOLERANCE):
    return isinstance(a, (int, float)) and isinstance(b, (int, float)) and math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance


def recompute(rows):
    requested = sum(r["requested_ms"] for r in rows)
    low_over = sum(r["overshoot_lower_ms"] for r in rows)
    high_over = sum(r["overshoot_upper_ms"] for r in rows)
    low_hold = sum(r["owner_commanded_hold_lower_ms"] for r in rows)
    high_hold = sum(r["owner_commanded_hold_upper_ms"] for r in rows)
    return {
        "completed_hold_count": len(rows),
        "requested_total_ms": requested,
        "owner_commanded_hold_total_lower_ms": low_hold,
        "owner_commanded_hold_total_upper_ms": high_hold,
        "overshoot_total_lower_ms": low_over,
        "overshoot_total_upper_ms": high_over,
        "median_overshoot_lower_ms": median([r["overshoot_lower_ms"] for r in rows]),
        "median_overshoot_upper_ms": median([r["overshoot_upper_ms"] for r in rows]),
        "overshoot_fraction_lower": low_over / requested,
        "overshoot_fraction_upper": high_over / requested,
    }


def compare_trace(name, candidate, table, expected_count):
    errors = []
    crows = candidate.get("completed_holds", [])
    trows = [r for r in table.get("completed_holds", []) if r.get("trace") == name]
    cindex = {(r.get("id"), r.get("step")): r for r in crows}
    tindex = {(r.get("decision_id"), r.get("step")): r for r in trows}
    if len(crows) != expected_count or len(cindex) != expected_count:
        errors.append(f"{name}: candidate row count/identity is not {expected_count}")
    if len(trows) != expected_count or len(tindex) != expected_count:
        errors.append(f"{name}: prior table row count/identity is not {expected_count}")
    if set(cindex) != set(tindex):
        errors.append(f"{name}: candidate and prior table row identities differ")

    for identity in sorted(set(cindex) & set(tindex), key=lambda x: (str(x[0]), x[1] if isinstance(x[1], int) else -1)):
        c, t = cindex[identity], tindex[identity]
        if c.get("classification") != "ordinary_completed_bounded":
            errors.append(f"{name} {identity}: unexpected candidate classification")
        if c.get("keys") != t.get("keys"):
            errors.append(f"{name} {identity}: keyset differs")
        if c.get("requested_ms") != t.get("requested_ms"):
            errors.append(f"{name} {identity}: requested duration differs")
        for candidate_key, table_key in (("owner_commanded_hold_lower_ms", "lower_ms"),
                                         ("owner_commanded_hold_upper_ms", "upper_ms"),
                                         ("bound_width_ms", "interval_width_ms")):
            if not near(c.get(candidate_key), t.get(table_key), DISPLAY_TOLERANCE_MS):
                errors.append(f"{name} {identity}: {candidate_key} does not match displayed {table_key}")

    derived = recompute(crows) if crows else {}
    summary = candidate.get("summary", {})
    for key, value in derived.items():
        if not near(summary.get(key), value):
            errors.append(f"{name}: candidate summary {key} does not match recomputation")
    prior_summary = table.get("reported_exact_precision_summaries", {}).get(name, {})
    mapping = {
        "completed_hold_count": "completed_holds",
        "interrupted_verified_count": "verified_interrupted_holds",
    }
    for key, prior_key in mapping.items():
        expected = len(candidate.get("interrupted_holds", [])) if key == "interrupted_verified_count" else len(crows)
        if prior_summary.get(prior_key) != expected or summary.get(key) != expected:
            errors.append(f"{name}: count {key} does not reconcile")
    for key in ("requested_total_ms", "owner_commanded_hold_total_lower_ms",
                "owner_commanded_hold_total_upper_ms", "overshoot_total_lower_ms",
                "overshoot_total_upper_ms", "median_overshoot_lower_ms", "median_overshoot_upper_ms"):
        if not near(derived.get(key), prior_summary.get(key)) or not near(derived.get(key), summary.get(key)):
            errors.append(f"{name}: exact aggregate {key} does not reconcile")
    return {"trace": name, "candidate_rows": len(crows), "prior_rows": len(trows),
            "matched_rows": len(set(cindex) & set(tindex)), "derived_summary": derived, "errors": errors}


def reconcile(v38, v39, table, expected_counts=(11, 27)):
    errors = []
    r38 = compare_trace("v38", v38, table, expected_counts[0])
    r39 = compare_trace("v39", v39, table, expected_counts[1])
    errors.extend(r38["errors"] + r39["errors"])
    ti = table.get("interrupted_hold")
    ci = v39.get("interrupted_holds", [])
    if not isinstance(ti, dict) or len(ci) != 1:
        errors.append("expected exactly one prior and candidate interrupted v39 hold")
    else:
        candidate_i = ci[0]
        fields = {"id": "decision_id", "step": "step", "requested_ms": "requested_ms", "keys": "keys",
                  "full_keyset_ack_ns": "full_keyset_ack_ns", "empty_verified_ns": "empty_verified_ns",
                  "ack_to_empty_verified_ms": "ack_to_empty_verified_ms", "classification": "classification"}
        for cf, tf in fields.items():
            if candidate_i.get(cf) != ti.get(tf):
                errors.append(f"interrupted v39: {cf} differs from prior table")
        if ti.get("excluded_from_completed_hold_totals") is not True:
            errors.append("prior table does not explicitly exclude interrupted row from completed totals")
        if v38.get("interrupted_holds"):
            errors.append("v38 candidate unexpectedly contains an interrupted row")
    return {"decision": "PASS_PRIOR_TABLE_RECONCILIATION_SCOPED" if not errors else "FAIL_PRIOR_TABLE_RECONCILIATION",
            "checks": {"v38": r38, "v39": r39}, "interrupted_v39_match": not any("interrupted v39" in e for e in errors),
            "errors": errors,
            "scope": "audit-only comparison of retained candidate JSON to prior rounded table and exact summaries"}


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: audit_reconcile.py CANDIDATE_V38 CANDIDATE_V39 PRIOR_TABLE OUTPUT")
    paths = [Path(x) for x in argv[1:4]]
    for p in paths:
        data = p.read_bytes()
        expected = EXPECTED_INPUT_SHA256.get(p.name)
        if expected is None or hashlib.sha256(data).hexdigest() != expected:
            raise SystemExit(f"STOP_INPUT_LOCAL_SHA256_MISMATCH: {p.name}")
    values = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    result = reconcile(*values)
    Path(argv[4]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["decision"].startswith("PASS_") else 1)


if __name__ == "__main__":
    main(sys.argv)
