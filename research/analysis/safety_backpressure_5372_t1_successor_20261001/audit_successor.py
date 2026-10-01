#!/usr/bin/env python3
"""Allocation-02 identity wrapper around the immutable T1 raw auditor."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ALLOCATION = "SAFETY-BACKPRESSURE-ENDOGENOUS-DEMAND-5372-T1-20261001-02"
HERE = Path(__file__).resolve().parent
DEFAULT_AUDITOR = HERE.parent / "safety_backpressure_5372_t1_v1" / "audit.py"


def audit_successor(rows: list[dict], auditor_path: Path = DEFAULT_AUDITOR) -> list[str]:
    errors = []
    if not rows or rows[0].get("type") != "freeze" or rows[0].get("allocation") != ALLOCATION:
        errors.append("successor freeze allocation mismatch")
    scenario_rows = [row for row in rows if row.get("type") == "scenario"]
    if len(scenario_rows) != 16 or any(row.get("allocation") != ALLOCATION for row in scenario_rows):
        errors.append("successor scenario allocation mismatch")
    spec = importlib.util.spec_from_file_location("frozen_t1_raw_auditor", auditor_path)
    if spec is None or spec.loader is None:
        return errors + ["could not load frozen independent auditor"]
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors.extend(module.audit(rows))
    return errors


def main() -> int:
    event_path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "candidate.jsonl"
    auditor_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_AUDITOR
    rows = [json.loads(line) for line in event_path.read_text().splitlines() if line.strip()]
    errors = audit_successor(rows, auditor_path)
    if errors:
        print("FAIL_SUCCESSOR_INDEPENDENT_AUDIT")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS_SUCCESSOR_INDEPENDENT_AUDIT allocation=02 cells=16 safety_all_serviced=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
