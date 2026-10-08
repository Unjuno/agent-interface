#!/usr/bin/env python3
"""Independent raw-only check for Issue #16 synthetic T4 rows."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

RAW = Path(__file__).with_name("raw") / "formal.jsonl"


def expected(r):
    applied = r["applied"]
    schedules = {
        "all_reversible": (("WRITE", True), ("LABEL", True), ("FORMAT", True), ("SAVE", True)),
        "irreversible_middle": (("WRITE", True), ("LABEL", True), ("SEND", False), ("ARCHIVE", True)),
        "irreversible_first": (("SEND", False), ("WRITE", True), ("LABEL", True)),
        "compensator_failure_control": (("WRITE", True), ("LABEL", True), ("FORMAT", True), ("SAVE", True)),
    }
    actions = schedules[r["case"]]
    stop = r["stop_after"]
    expected_applied = [name for name, _ in actions[:stop]]
    if applied != expected_applied or stop < 0 or stop >= len(actions):
        raise ValueError("non-canonical or non-interrupted prefix")
    reversible = all(flag for _, flag in actions[:stop])
    failed = r["case"] == "compensator_failure_control"
    comp = bool(applied) and reversible and not failed
    baseline = "ABORTED_NO_EFFECT" if not applied else "UNKNOWN"
    saga = "ABORTED_NO_EFFECT" if not applied else "ABORTED_COMPENSATED" if comp else "ABORTED_PARTIAL"
    baseline_unresolved = bool(applied and reversible)
    saga_unresolved = bool(applied and reversible and not comp)
    return baseline, saga, comp, expected_applied, [name for name, _ in actions], baseline_unresolved, saga_unresolved


def main():
    lines = RAW.read_text(encoding="utf-8").splitlines()
    errors = []
    seen = set()
    covered = set()
    for i, line in enumerate(lines):
        r = json.loads(line)
        try:
            baseline, saga, comp, expected_applied, expected_actions, baseline_unresolved, saga_unresolved = expected(r)
        except (KeyError, ValueError, TypeError) as exc:
            errors.append(f"row {i}: invalid case/prefix: {exc}")
            continue
        identity_payload = {k: v for k, v in r.items() if k != "record_id"}
        identity = hashlib.sha256(json.dumps(identity_payload, sort_keys=True).encode()).hexdigest()
        if r.get("record_id") != identity:
            errors.append(f"row {i}: record id mismatch")
        if r["baseline"] != baseline or r["saga"] != saga or r["compensation_verified"] != comp:
            errors.append(f"row {i}: saga classification mismatch")
        if r["baseline"] == "COMMITTED" or r["saga"] == "COMMITTED":
            errors.append(f"row {i}: interrupted case committed")
        if r["history_preserved"] != r["applied"]:
            errors.append(f"row {i}: effect history lost")
        if r["actions"] != expected_actions:
            errors.append(f"row {i}: malformed action schedule")
        if r["unresolved_compensatable_prefix_baseline"] != baseline_unresolved or r["unresolved_compensatable_prefix_saga"] != saga_unresolved:
            errors.append(f"row {i}: unresolved-prefix metric mismatch")
        if r["forbidden_commit"]:
            errors.append(f"row {i}: forbidden commit flag set")
        covered.add((r["case"], r["stop_after"]))
        if r["record_id"] in seen:
            errors.append(f"row {i}: duplicate record id")
        seen.add(r["record_id"])
    expected_coverage = {(case, stop) for case, n in (("all_reversible", 4), ("irreversible_middle", 4), ("irreversible_first", 3)) for stop in range(n)} | {("compensator_failure_control", 2)}
    if len(lines) != 10 or covered != expected_coverage:
        errors.append(f"expected 10 fixed cases; observed {len(lines)}")
    print(json.dumps({"status": "PASS_SCOPED" if not errors else "FAIL_AUDIT", "rows": len(lines), "errors": errors}, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
