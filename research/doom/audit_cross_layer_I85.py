"""Raw-only auditor for the frozen I85 cross-layer decision matrix."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
cases = json.loads((HERE / "raw-cases.json").read_text(encoding="utf-8"))["cases"]
candidate = json.load(sys.stdin)
expected = {row["case"]: row for row in cases}
errors = []
rows = candidate.get("results")
if not isinstance(rows, list) or len(rows) != len(expected):
    errors.append({"field": "result_count", "expected": len(expected),
                   "actual": len(rows) if isinstance(rows, list) else None})
else:
    seen = set()
    for row in rows:
        name = row.get("case")
        if name not in expected or name in seen:
            errors.append({"case": name, "field": "case_identity"})
            continue
        seen.add(name)
        rule = expected[name]
        receipt = row.get("producer_receipt", {})
        consumer = row.get("consumer_result", {})
        checks = {
            "producer_verified": row.get("producer_verified") is rule["producer_verified"],
            "receipt_verification": receipt.get("owner_transition_verified") is rule["producer_verified"],
            "measurement_ready": consumer.get("measurement_ready") is rule["measurement_ready"],
            "hold_count": consumer.get("hold_count") == rule["hold_count"],
        }
        if "invalid_release_count" in rule:
            checks["invalid_release_count"] = consumer.get("invalid_release_count") == rule["invalid_release_count"]
        if name == "cleanup_inside_release_bracket":
            recs = row.get("owner_records", [])
            checks["cleanup_overlap"] = (
                receipt.get("owner_cleanup_log_available") is True
                and receipt.get("owner_cleanup_overlapped_release_call") is True
                and receipt.get("ordinary_release_candidate_at_request") is True
                and receipt.get("ordinary_release_candidate") is False
                and len(recs) == 1
                and type(recs[0].get("verified_ns")) is int
                and receipt["release_call_started_ns"] <= recs[0]["verified_ns"] <= receipt["release_call_returned_ns"]
            )
        if name == "prior_cleanup_outside_bracket":
            checks["prior_cleanup_not_poisoning"] = (
                receipt.get("owner_cleanup_log_available") is True
                and receipt.get("owner_cleanup_overlapped_release_call") is False
                and receipt.get("ordinary_release_candidate") is True
            )
        bad = [field for field, ok in checks.items() if not ok]
        errors.extend({"case": name, "field": field} for field in bad)
    if seen != set(expected):
        errors.append({"field": "missing_cases", "actual": sorted(set(expected) - seen)})

summary = {
    "schema": "map01-release-producer-analyzer-cross-layer-audit-I85-v1",
    "case_count": len(rows) if isinstance(rows, list) else 0,
    "errors": errors,
    "decision": "PASS_CROSS_LAYER_CONSTRUCTION" if not errors else "FAIL",
    "scope": "frozen synthetic producer/analyzer composition only",
}
print(json.dumps(summary, indent=2, sort_keys=True))
if errors:
    raise SystemExit(1)
