"""Independent raw-only audit; does not import candidate gate code."""

import hashlib
import json
import sys
from pathlib import Path


EXPECTED = {
    "stationary_complete": "ELIGIBLE_REFERENCE",
    "declared_unseen_cleanup": "NOT_ESTIMABLE_MODE_COVERAGE",
    "insufficient_cleanup_tail_events": "NOT_ESTIMABLE_INSUFFICIENT_TAIL_EVENTS",
    "declared_drift": "NOT_ESTIMABLE_NONSTATIONARY",
    "dependence_unchecked": "NOT_ESTIMABLE_DEPENDENCE",
    "right_censored": "NOT_ESTIMABLE_CENSORED_ENDPOINT",
    "missing_neutral": "NOT_ESTIMABLE_MISSING_ENDPOINT",
}


def main() -> int:
    source = Path(sys.argv[1])
    candidate = Path(sys.argv[2])
    cases_raw = source.read_bytes()
    result = json.loads(candidate.read_text())
    rows = result.get("rows")
    if result.get("input_sha256") != hashlib.sha256(cases_raw).hexdigest():
        raise SystemExit("FAIL_INPUT_HASH")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        raise SystemExit("FAIL_ROW_COUNT")
    observed = {row.get("case_id"): row.get("decision") for row in rows}
    if observed != EXPECTED:
        raise SystemExit(f"FAIL_DECISIONS observed={observed!r}")
    print(f"PASS_RAW_ONLY rows={len(rows)} controls={len(EXPECTED) - 1} errors=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
