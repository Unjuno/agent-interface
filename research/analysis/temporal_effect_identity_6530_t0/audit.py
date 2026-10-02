#!/usr/bin/env python3
"""Independent raw-only auditor. Does not import or execute candidate code."""
import json
import sys
from pathlib import Path


def main() -> int:
    raw_path, truth_path, out_path = map(Path, sys.argv[1:4])
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    truth = json.loads(truth_path.read_text(encoding="utf-8"))["expected"]
    rows = raw.get("rows", [])
    by_id = {row.get("id"): row for row in rows}
    errors = []
    if len(rows) != len(truth) or len(by_id) != len(rows) or set(by_id) != set(truth):
        errors.append("case_roster_mismatch")
    for case_id, expected in truth.items():
        row = by_id.get(case_id)
        if row is None:
            continue
        got = row.get("typed", {})
        if got.get("classification") != expected["classification"]:
            errors.append(f"{case_id}:classification")
        if "utc" in expected and got.get("expected_utc") != expected["utc"]:
            errors.append(f"{case_id}:utc")
        if "expected_utc_occurrences" in expected:
            if got.get("expected_utc_occurrences") != expected["expected_utc_occurrences"]:
                errors.append(f"{case_id}:recurrence_truth")
        if case_id == "local-recurrence":
            if not row.get("string_only_accept") or not row.get("offset_only_accept"):
                errors.append("recurrence_baseline_did_not_accept")
        if case_id == "fold-unresolved":
            opts = got.get("possible_utc", [])
            if sorted(opts) != sorted(expected["utc_options"]):
                errors.append("fold_options_mismatch")
    result = {"audit": "PASS" if not errors else "FAIL",
              "rows": len(rows), "errors": errors}
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
