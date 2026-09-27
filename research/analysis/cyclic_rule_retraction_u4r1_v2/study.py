#!/usr/bin/env python3
"""Finite candidate experiment for Issue #4449."""
import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOTS = frozenset({"E0", "E1"})
CLAIMS = ("A", "B")
RULES = (
    ("r0", "A", ("E0",)),
    ("r1", "A", ("B",)),
    ("r2", "A", ("E1", "B")),
    ("r3", "B", ("E1",)),
    ("r4", "B", ("A",)),
    ("r5", "B", ("E0", "A")),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grounded(active):
    known = set(ROOTS)
    changed = True
    while changed:
        changed = False
        for _, head, body in active:
            if set(body) <= known and head not in known:
                known.add(head)
                changed = True
    return frozenset(known & set(CLAIMS))


def affected_cone(deleted, active):
    cone = {deleted[1]}
    changed = True
    while changed:
        changed = False
        for _, head, body in active:
            if head not in cone and set(body) & cone:
                cone.add(head)
                changed = True
    return frozenset(cone)


def clear_and_rederive(old, active, cone):
    known = set(ROOTS) | (set(old) - set(cone))
    changed = True
    while changed:
        changed = False
        for _, head, body in active:
            if head in cone and set(body) <= known and head not in known:
                known.add(head)
                changed = True
    return frozenset(known & set(CLAIMS))


def local_support(old, active):
    known = set(ROOTS) | set(old)
    changed = True
    while changed:
        changed = False
        for claim in CLAIMS:
            if claim in known and not any(
                head == claim and set(body) <= known for _, head, body in active
            ):
                known.remove(claim)
                changed = True
    return frozenset(known & set(CLAIMS))


def blind_invalidate(old, cone):
    return frozenset(set(old) - set(cone))


def row_for(mask, deleted_id=None):
    before_active = tuple(rule for i, rule in enumerate(RULES) if mask & (1 << i))
    before = grounded(before_active)
    if deleted_id is None:
        active = before_active
        cone = frozenset()
        candidate = full = local = blind = before
    else:
        deleted = next(rule for rule in before_active if rule[0] == deleted_id)
        active = tuple(rule for rule in before_active if rule[0] != deleted_id)
        cone = affected_cone(deleted, active)
        candidate = clear_and_rederive(before, active, cone)
        full = grounded(active)
        local = local_support(before, active)
        blind = blind_invalidate(before, cone)
    return {
        "mask": mask,
        "deleted_rule": deleted_id,
        "active_rules_before": [rule[0] for rule in before_active],
        "active_rules_after": [rule[0] for rule in active],
        "before": sorted(before),
        "affected_cone": sorted(cone),
        "clear_and_rederive": sorted(candidate),
        "full_rebuild": sorted(full),
        "local_support": sorted(local),
        "blind_invalidate": sorted(blind),
    }


def conditions():
    for mask in range(64):
        yield row_for(mask)
        for i, (rule_id, _, _) in enumerate(RULES):
            if mask & (1 << i):
                yield row_for(mask, rule_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("construction", "formal"), required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit("OUTPUT_NOT_EMPTY")
    out.mkdir(parents=True, exist_ok=True)
    all_rows = list(conditions())
    if args.phase == "construction":
        rows = [r for r in all_rows if r["mask"] in {1, 11, 19}]
    else:
        rows = all_rows
    canonical = "".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in rows).encode()
    input_obj = {
        "roots": sorted(ROOTS),
        "claims": list(CLAIMS),
        "rules": [{"id": rid, "head": head, "body": list(body)} for rid, head, body in RULES],
        "expected_conditions": len(rows),
    }
    conditions_bytes = "".join(
        json.dumps({"mask": r["mask"], "deleted_rule": r["deleted_rule"]}, sort_keys=True, separators=(",", ":")) + "\n"
        for r in rows
    ).encode()
    input_bytes = (json.dumps(input_obj, sort_keys=True, indent=2) + "\n").encode()
    (out / "input.json").write_bytes(input_bytes)
    (out / "conditions.jsonl").write_bytes(conditions_bytes)
    started = time.time_ns()
    (out / "rows.jsonl").write_bytes(canonical)
    ended = time.time_ns()
    receipt = {
        "schema": "cyclic-rule-retraction-process-v1",
        "phase": args.phase,
        "pid": os.getpid(),
        "exit_code": 0,
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "started_ns": started,
        "ended_ns": ended,
        "rows": len(rows),
        "input_sha256": digest(input_bytes),
        "conditions_sha256": digest(conditions_bytes),
        "rows_sha256": digest(canonical),
        "study_sha256": digest(Path(__file__).read_bytes()),
    }
    (out / "process.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"phase": args.phase, "rows": len(rows), "rows_sha256": receipt["rows_sha256"], "exit_code": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
