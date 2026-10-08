#!/usr/bin/env python3
"""Deterministic paired policy probe for Issue #16; synthetic only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

OUT = Path(__file__).with_name("raw") / "formal.jsonl"


def simulate(actions: tuple[tuple[str, bool], ...], stop_after: int, fail_comp: bool = False):
    applied = actions[:stop_after]
    reversible = all(can_compensate for _, can_compensate in applied)
    comp_ok = bool(applied) and reversible and not fail_comp
    saga = "ABORTED_NO_EFFECT" if not applied else ("ABORTED_COMPENSATED" if comp_ok else "ABORTED_PARTIAL")
    # The monolithic baseline has no independently verified per-effect recovery contract.
    baseline = "ABORTED_NO_EFFECT" if not applied else "UNKNOWN"
    return {
        "actions": [name for name, _ in actions],
        "stop_after": stop_after,
        "applied": [name for name, _ in applied],
        "baseline": baseline,
        "saga": saga,
        "history_preserved": list(name for name, _ in applied),
        "compensation_verified": comp_ok,
        "forbidden_commit": baseline == "COMMITTED" or saga == "COMMITTED",
        "unresolved_compensatable_prefix_baseline": bool(applied and reversible),
        "unresolved_compensatable_prefix_saga": bool(applied and reversible and not comp_ok),
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    schedules = {
        "all_reversible": (("WRITE", True), ("LABEL", True), ("FORMAT", True), ("SAVE", True)),
        "irreversible_middle": (("WRITE", True), ("LABEL", True), ("SEND", False), ("ARCHIVE", True)),
        "irreversible_first": (("SEND", False), ("WRITE", True), ("LABEL", True)),
    }
    rows = []
    for case, actions in schedules.items():
        # Only interrupted prefixes are scored here; the full successful execution
        # is outside this interruption-only comparison.
        for stop in range(len(actions)):
            row = {"case": case, **simulate(actions, stop)}
            row["record_id"] = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
            rows.append(row)
    # An explicit compensator-failure control must not receive compensated status.
    actions = schedules["all_reversible"]
    rows.append({"case": "compensator_failure_control", **simulate(actions, 2, fail_comp=True)})
    OUT.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    eligible = sum(r["unresolved_compensatable_prefix_baseline"] for r in rows)
    remaining = sum(r["unresolved_compensatable_prefix_saga"] for r in rows)
    print(json.dumps({"rows": len(rows), "eligible_compensatable_prefixes": eligible,
                      "unresolved_after_saga": remaining, "raw_path": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
