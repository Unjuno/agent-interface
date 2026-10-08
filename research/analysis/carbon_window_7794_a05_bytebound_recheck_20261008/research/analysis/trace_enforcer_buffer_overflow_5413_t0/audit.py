"""Independent raw-only reference audit; deliberately does not import runner."""

import json
import sys


def expected(events, commit, capacity, policy):
    overflow = len(events) > capacity
    if overflow and policy == "FAIL_CLOSED":
        return "UNKNOWN_BUFFER_OVERFLOW", False, overflow
    visible = events[:capacity] if policy == "DROP_NEWEST" else events
    obs = [e for e in visible if e.get("kind") == "OBSERVE"]
    auth = [e for e in visible if e.get("kind") == "AUTHORITY"]
    mutated = any(e.get("kind") == "EXTERNAL_MUTATION" for e in visible)
    authorized = any(
        o.get("target") == commit.get("target") == a.get("target")
        and o.get("epoch") == commit.get("epoch") == a.get("epoch")
        for o in obs
        for a in auth
    )
    if not authorized or mutated:
        return "BLOCK", False, overflow
    return "PASS", True, overflow


def audit(path):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    errors = []
    keys = set()
    for i, row in enumerate(rows):
        key = (row.get("case_id"), row.get("policy"))
        if key in keys:
            errors.append(f"row {i}: duplicate cell")
        keys.add(key)
        want = expected(
            row.get("events", []), row.get("commit", {}),
            row.get("capacity", -1), row.get("policy", ""),
        )
        got = (row.get("decision"), row.get("effect_emitted"), row.get("overflow"))
        if got != want:
            errors.append(f"row {i}: {got!r} != {want!r}")
        retained = row.get("events", [])[:row.get("capacity", 0)] if row.get("policy") == "DROP_NEWEST" else row.get("events", [])
        if row.get("retained_event_kinds") != [e.get("kind") for e in retained]:
            errors.append(f"row {i}: retained-event trace mismatch")
    required = {(case, policy) for case in ("exact_control", "dropped_mutation", "irrelevant_overflow") for policy in ("FAIL_CLOSED", "DROP_NEWEST")}
    if keys != required:
        errors.append(f"matrix mismatch: got {len(keys)} cells, expected {len(required)}")
    print(json.dumps({"rows": len(rows), "errors": errors, "audit": "PASS" if not errors else "FAIL"}, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(audit(sys.argv[1]))
