#!/usr/bin/env python3
"""Fail closed if the Issue #57 composition plan loses a frozen requirement."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "research" / "live_control" / "INTEGRATED_EFFICIENCY_PLAN_V1.md"

REQUIRED = {
    "three_arms": (
        "A — plain visual program",
        "B — current optimized, ephemeral",
        "C — integrated persistent",
    ),
    "six_tasks": tuple(f"{index}." for index in range(1, 7)),
    "comparison_phases": ("cold task", "warm-equivalent", "invalidation/repair", "post-repair"),
    "accounting": (
        "actual model attempts and completions",
        "input/cached/cache-write/output/reasoning tokens",
        "model-visible images",
        "planner generations",
        "local observations",
        "pointer admissions",
        "releases",
    ),
    "hard_safety": (
        "zero old-target pointer admissions",
        "exact expected token once",
        "No failed side effect is retried",
    ),
    "decision": ("RETAIN requires", "HOLD applies", "REJECT applies"),
    "integration_gap": ("existing_requirement_regression", "interface_mismatch",
                        "integration_capability_gap", "benchmark_setup_accounting_defect",
                        "integrated_efficiency_discoveries_v1.json",
                        "preregister a new finite block"),
    "doom_realtime": (
        "freedoom2.wad",
        "MAP01",
        "keep asynchronous 35-tic game time running during model waits",
        "No pause, save-state stepping, API action injection",
    ),
}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    text = PLAN.read_text(encoding="utf-8")
    searchable = " ".join(text.split()).casefold()
    checks = {
        group: {needle: needle.casefold() in searchable for needle in needles}
        for group, needles in REQUIRED.items()
    }
    missing = [
        f"{group}: {needle}"
        for group, entries in checks.items()
        for needle, present in entries.items()
        if not present
    ]
    result = {
        "schema": "integrated_efficiency_plan_audit_v1",
        "plan": PLAN.relative_to(ROOT).as_posix(),
        "plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        "checks": checks,
        "missing": missing,
        "ok": not missing,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
