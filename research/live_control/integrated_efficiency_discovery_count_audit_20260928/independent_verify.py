from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path


NUMBER = {"six": 6, "seven": 7, "eight": 8}


def declared_counts(plan: str) -> list[int]:
    normalized = re.sub(r"\s+", " ", plan).lower()
    patterns = (
        r"the (six|seven|eight) current discoveries",
        r"(six|seven|eight) retained pre-prereg discoveries",
    )
    found = []
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            found.append(NUMBER[match.group(1)])
    return found


def consistency(plan: str, ledger: list[dict]) -> bool:
    counts = collections.Counter(row.get("class") for row in ledger)
    declarations = declared_counts(plan)
    return (
        len(ledger) == 8
        and declarations == [8, 8]
        and counts == {"interface_mismatch": 3, "benchmark_setup_accounting_defect": 5}
        and len({row.get("id") for row in ledger}) == 8
        and all(row.get("regression_test") for row in ledger)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    plan = args.plan.read_text(encoding="utf-8")
    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    before = declared_counts(plan)
    raw_consistent = (
        raw.get("ledger_entries") == len(ledger)
        and raw.get("class_counts") == dict(sorted(collections.Counter(r.get("class") for r in ledger).items()))
        and raw.get("unique_ids") == len({r.get("id") for r in ledger})
    )
    normalized = re.sub(r"\s+", " ", plan)
    repaired = re.sub(r"\bthe six current discoveries\b", "the eight current discoveries", normalized, flags=re.IGNORECASE)
    repaired = re.sub(r"\bsix retained pre-prereg discoveries\b", "eight retained pre-prereg discoveries", repaired, flags=re.IGNORECASE)
    controls = {
        "raw_matches_independent_ledger_reconstruction": raw_consistent,
        "original_plan_count_claims_are_both_six": before == [6, 6],
        "replacing_claims_with_eight_restores_consistency": consistency(repaired, ledger),
        "one_count_mutation_is_rejected": not consistency(repaired.replace("eight retained pre-prereg", "seven retained pre-prereg", 1), ledger),
    }
    errors = [name for name, ok in controls.items() if not ok]
    report = {
        "schema": "integrated-efficiency-discovery-count-independent-audit-v1",
        "status": "PASS_RAW_AND_DISCREPANCY_RECONSTRUCTED_SCOPED" if not errors else "HOLD_INDEPENDENT_RECONSTRUCTION_FAILED",
        "raw_runner_status": raw.get("status"),
        "independent_ledger_entries": len(ledger),
        "independent_class_counts": dict(sorted(collections.Counter(r.get("class") for r in ledger).items())),
        "original_plan_count_claims": before,
        "controls": controls,
        "errors": errors,
        "scope": "Plan/ledger bookkeeping only; no experimental runtime or efficiency inference.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
