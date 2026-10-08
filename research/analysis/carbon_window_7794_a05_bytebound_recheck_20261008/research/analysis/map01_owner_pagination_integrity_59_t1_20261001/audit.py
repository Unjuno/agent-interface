"""Independent raw-only audit of the bounded owner pagination experiment."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def audit(raw_path: Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = []
    cases = raw.get("cases")
    if not isinstance(cases, list) or len(cases) != raw.get("case_count"):
        errors.append("case_count_mismatch")
        cases = []
    expected = []
    for case in cases:
        ids = case.get("full_run_ids", [])
        visible = case.get("visible_run_ids", [])
        current = case.get("current_run_id")
        complete = len(set(visible)) == len(set(ids))
        oracle = bool(ids) and current == min(ids)
        incomplete = not complete
        if case.get("incomplete") != incomplete or case.get("oracle_admitted") != oracle:
            errors.append("independent_oracle_disagreement")
        if incomplete and case.get("helper_admitted") and not oracle:
            expected.append(case)
    if len(expected) != raw.get("counterexample_count"):
        errors.append("counterexample_count_mismatch")
    if expected != raw.get("counterexamples"):
        errors.append("counterexample_rows_mismatch")
    decision = "PASS_BOUNDED_FAIL_CLOSED_GAP_FOUND" if expected else "HOLD_NO_GAP_IN_BOUNDED_MODEL"
    if raw.get("decision") != decision:
        errors.append("decision_mismatch")
    return {
        "schema": "map01-owner-pagination-integrity-59-t1-audit-v1",
        "passed": not errors,
        "errors": errors,
        "case_count": len(cases),
        "counterexample_count": len(expected),
        "decision": decision,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "audit_scope": "independent set/cardinality and earliest-run oracle; synthetic evidence only",
    }


if __name__ == "__main__":
    import sys

    print(json.dumps(audit(Path(sys.argv[1])), indent=2, sort_keys=True))
