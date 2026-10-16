from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    plan = args.plan.read_text(encoding="utf-8")
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    counts = collections.Counter(row.get("class") for row in ledger)
    ids = [row.get("id") for row in ledger]
    declarations = {
        "current_discoveries": re.search(r"The (\w+) current discoveries", plan),
        "retained_pre_prereg": re.search(r"(\w+) retained pre-prereg discoveries", plan),
    }
    words = {"six": 6, "seven": 7, "eight": 8}
    declared = {
        key: words.get(match.group(1).lower()) if match else None
        for key, match in declarations.items()
    }
    missing_fields = [
        index for index, row in enumerate(ledger)
        if not all(row.get(field) for field in ("id", "class", "status", "regression_test"))
    ]
    errors = []
    if any(value is None for value in declared.values()):
        errors.append("plan_count_declaration_missing_or_unrecognized")
    if any(value != len(ledger) for value in declared.values()):
        errors.append("plan_ledger_count_mismatch")
    if counts != {"interface_mismatch": 3, "benchmark_setup_accounting_defect": 5}:
        errors.append("ledger_class_counts_mismatch")
    if len(ids) != len(set(ids)):
        errors.append("duplicate_discovery_id")
    if missing_fields:
        errors.append("required_provenance_fields_missing")

    report = {
        "schema": "integrated-efficiency-discovery-count-audit-result-v1",
        "status": "PASS_DISCOVERY_LEDGER_COUNTS_SCOPED" if not errors else "FAIL_PLAN_LEDGER_COUNT_INCONSISTENCY",
        "ledger_entries": len(ledger),
        "class_counts": dict(sorted(counts.items())),
        "plan_count_declarations": declared,
        "unique_ids": len(set(ids)),
        "missing_required_field_rows": missing_fields,
        "errors": errors,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
