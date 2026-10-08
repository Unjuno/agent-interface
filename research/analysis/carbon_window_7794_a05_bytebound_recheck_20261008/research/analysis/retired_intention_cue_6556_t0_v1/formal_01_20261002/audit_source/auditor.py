"""Independent raw-only auditor for Issue #6556; does not import candidate."""
import json
import sys
from pathlib import Path


def audit(fixture, oracle, raw):
    errors, unsafe, missed, misattributed = [], [], [], []
    cases = {c["id"]: c for c in fixture["cases"]}
    truths = oracle["truth"]
    expected_keys = {(c["id"], p) for c in fixture["cases"] for p in fixture["policies"]}
    seen = set()
    for row in raw.get("rows", []):
        key = (row.get("case_id"), row.get("policy"))
        if key in seen:
            errors.append({"kind": "duplicate_row", "key": key})
            continue
        seen.add(key)
        case, truth = cases.get(key[0]), truths.get(key[0])
        if case is None or truth is None or key not in expected_keys:
            errors.append({"kind": "unknown_row", "key": key})
            continue
        admitted = row.get("decision") == "ADMIT"
        if admitted and not truth["eligible"]:
            unsafe.append({"case_id": key[0], "policy": key[1], "oracle_reason": truth["reason"]})
        if truth["eligible"] and not admitted:
            missed.append({"case_id": key[0], "policy": key[1], "decision": row.get("decision")})
        if row.get("obligation_status") != case["obligation"] or row.get("effect_resolved") is not False or row.get("release_resolved") is not False:
            errors.append({"kind": "obligation_laundering", "key": key})
        expected_lineage = truth["origin"]["instance"] if admitted else None
        if admitted and row.get("response_lineage") != expected_lineage:
            misattributed.append({"case_id": key[0], "policy": key[1], "true_origin": expected_lineage, "claimed_lineage": row.get("response_lineage")})
            if key[1] == "ORIGIN_GENERATION_RETIREMENT_FENCE":
                errors.append({"kind": "origin_fence_misattributed_fresh_response", "key": key})
        elif not admitted and row.get("response_lineage") is not None:
            errors.append({"kind": "refused_row_has_response_lineage", "key": key, "observed": row.get("response_lineage")})
        if key[1] == "ORIGIN_GENERATION_RETIREMENT_FENCE":
            if truth["origin"] != case["event"]["origin"] and row.get("decision") != "UNKNOWN":
                errors.append({"kind": "missing_origin_not_unknown", "case_id": key[0]})
    missing = sorted(expected_keys - seen)
    extra = sorted(seen - expected_keys)
    if missing or extra:
        errors.append({"kind": "denominator_mismatch", "expected": len(expected_keys), "observed": len(seen), "missing": missing, "extra": extra})
    fence_rows = [r for r in raw.get("rows", []) if r.get("policy") == "ORIGIN_GENERATION_RETIREMENT_FENCE"]
    fence_unsafe = [x for x in unsafe if x["policy"] == "ORIGIN_GENERATION_RETIREMENT_FENCE"]
    fence_missed = [x for x in missed if x["policy"] == "ORIGIN_GENERATION_RETIREMENT_FENCE"]
    status = "METHOD_PASS_SCOPED" if not errors and not fence_unsafe and not fence_missed and len(fence_rows) == len(cases) else "FAIL_OR_HOLD"
    return {
        "schema": "issue-6556-t0-audit-v1", "status": status,
        "rows_expected": len(expected_keys), "rows_seen": len(seen),
        "errors": errors, "unsafe_admissions_by_policy": _counts(unsafe),
        "missed_eligible_by_policy": _counts(missed),
        "misattributed_admissions_by_policy": _counts(misattributed),
        "origin_fence_unknown_cases": sorted(r["case_id"] for r in fence_rows if r["decision"] == "UNKNOWN"),
        "obligations_preserved_rows": len(raw.get("rows", [])) if not any(e["kind"] == "obligation_laundering" for e in errors) else None
    }


def _counts(rows):
    counts = {}
    for row in rows:
        counts[row["policy"]] = counts.get(row["policy"], 0) + 1
    return counts


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: auditor.py FIXTURE.json ORACLE.json CANDIDATE_RAW.json OUTPUT.json")
    fixture, oracle, raw = [json.loads(Path(p).read_text(encoding="utf-8")) for p in argv[1:4]]
    result = audit(fixture, oracle, raw)
    Path(argv[4]).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(result["status"], "errors", len(result["errors"]))
    if result["status"] != "METHOD_PASS_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main(sys.argv)
