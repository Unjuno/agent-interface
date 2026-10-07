from __future__ import annotations

import json
import sys
from pathlib import Path

EXPECTED = {
    "explicit_empty_control": "accepted",
    "held_key": "rejected",
    "held_button": "rejected",
    "missing_keys_down": "rejected",
    "missing_buttons_down": "rejected",
    "verified_false": "rejected",
    "missing_release": "rejected",
}


def audit(raw: dict) -> dict:
    rows = raw.get("cases")
    if type(rows) is not list or len(rows) != len(EXPECTED):
        return {"audit": "FAIL_RAW_SHAPE", "errors": ["case row count mismatch"]}
    seen = {}
    for row in rows:
        if type(row) is not dict or row.get("case") not in EXPECTED:
            return {"audit": "FAIL_RAW_SHAPE", "errors": ["unknown or malformed row"]}
        case_id = row["case"]
        if case_id in seen:
            return {"audit": "FAIL_RAW_SHAPE", "errors": ["duplicate case"]}
        seen[case_id] = row.get("outcome")
    disagreements = [case_id for case_id, outcome in EXPECTED.items() if seen.get(case_id) != outcome]
    unexpected_accepts = [case_id for case_id in EXPECTED if case_id != "explicit_empty_control" and seen.get(case_id) == "accepted"]
    unexpected_rejections = [case_id for case_id in EXPECTED if case_id == "explicit_empty_control" and seen.get(case_id) == "rejected"]
    if unexpected_accepts and not unexpected_rejections and all(
        seen.get(case_id) == EXPECTED[case_id]
        for case_id in EXPECTED
        if case_id not in unexpected_accepts
    ):
        disposition = "PASS_GAP_REPRODUCED"
    elif not disagreements:
        disposition = "PASS_CONTRACT"
    else:
        disposition = "HOLD_UNEXPECTED_DISPOSITION"
    return {
        "audit": disposition,
        "expected": EXPECTED,
        "observed": seen,
        "disagreements": disagreements,
        "errors": [],
        "unexpected_accepts": unexpected_accepts,
        "unexpected_rejections": unexpected_rejections,
    }


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("raw.json")
    result = audit(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["audit"] in {"PASS_GAP_REPRODUCED", "PASS_CONTRACT"} and not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
