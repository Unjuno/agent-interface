from __future__ import annotations

import collections
import argparse
import json
import re
from pathlib import Path


NUMBER = {"six": 6, "seven": 7, "eight": 8}


def extract(plan: str) -> list[int]:
    plan = re.sub(r"\s+", " ", plan).lower()
    patterns = (
        r"the (six|seven|eight) current discoveries",
        r"(six|seven|eight) retained pre-prereg discoveries",
    )
    return [NUMBER[m.group(1)] for p in patterns if (m := re.search(p, plan))]


def consistent(plan: str, ledger: list[dict]) -> bool:
    return (
        len(ledger) == 8
        and extract(plan) == [8, 8]
        and collections.Counter(r.get("class") for r in ledger)
        == {"interface_mismatch": 3, "benchmark_setup_accounting_defect": 5}
        and len({r.get("id") for r in ledger}) == 8
        and all(r.get("regression_test") for r in ledger)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root = args.root
    plan = (root / "research/live_control/INTEGRATED_EFFICIENCY_PLAN_V1.md").read_text(encoding="utf-8")
    ledger = json.loads((root / "research/live_control/integrated_efficiency_discoveries_v1.json").read_text(encoding="utf-8"))
    mutated = plan.replace("Eight retained pre-prereg discoveries", "Seven retained pre-prereg discoveries", 1)
    controls = {
        "corrected_plan_matches_ledger": consistent(plan, ledger),
        "count_mutation_is_rejected": not consistent(mutated, ledger),
        "both_count_claims_parse_across_wrapped_whitespace": extract(plan) == [8, 8],
    }
    errors = [name for name, passed in controls.items() if not passed]
    report = {
        "schema": "integrated-efficiency-corrected-discovery-count-validation-v1",
        "status": "PASS_CORRECTED_DISCOVERY_COUNTS_SCOPED" if not errors else "FAIL_CORRECTED_DISCOVERY_COUNTS",
        "ledger_entries": len(ledger),
        "class_counts": dict(sorted(collections.Counter(r.get("class") for r in ledger).items())),
        "plan_count_claims": extract(plan),
        "controls": controls,
        "errors": errors,
        "scope": "Bookkeeping consistency only; no runtime or efficiency inference.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
