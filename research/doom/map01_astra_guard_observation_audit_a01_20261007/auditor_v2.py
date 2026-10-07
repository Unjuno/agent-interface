"""Recursive raw-only audit and nested-field mutation controls for A01."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))

GUARD_KEYS = {
    "policy_invalidation", "cover_validity_admission",
    "cover_validity_soft_events", "planner_interrupt",
}
SIGNAL_EVENTS = {
    "health_signal", "ammo_signal", "policy_invalidation",
    "running_action_invalidation",
}


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(value, path="$", stack=None):
    if stack is None:
        stack = [(path, value)]
    while stack:
        current_path, current = stack.pop()
        yield current_path, current
        if isinstance(current, dict):
            for key, child in current.items():
                stack.append((f"{current_path}.{key}", child))
        elif isinstance(current, list):
            for index, child in enumerate(current):
                stack.append((f"{current_path}[{index}]", child))


def find_signal_paths(tree):
    found = []
    for path, value in records(tree):
        if not isinstance(value, dict):
            continue
        if value.get("event") in ("health_signal", "ammo_signal"):
            found.append(path)
        if value.get("signal_id") in ("health", "ammo") and "value" in value:
            found.append(path)
    return sorted(set(found))


def find_invalidation_paths(tree):
    return sorted({path for path, value in records(tree)
                   if isinstance(value, dict) and
                   value.get("event") in ("policy_invalidation",
                                           "running_action_invalidation")})


def find_guard_decision_paths(decisions):
    return sorted({path for path, value in records(decisions)
                   if isinstance(value, dict) and GUARD_KEYS.intersection(value)})


def audit():
    errors = []
    input_paths = {name: ROOT / name for name in FREEZE["inputs"]}
    hashes = {name: hash_file(path) for name, path in input_paths.items()}
    if hashes != FREEZE["inputs"]:
        errors.append("frozen input hashes differ")
    events = [json.loads(line) for line in input_paths[
        "research/doom/results/map01-astra-attempt-v1/events.jsonl"
    ].read_text(encoding="utf-8").splitlines()]
    report = json.loads(input_paths[
        "research/doom/results/map01-astra-attempt-v1/report.json"
    ].read_text(encoding="utf-8"))
    result = json.loads((PACKAGE / "results" / "a01.json").read_text(encoding="utf-8"))

    signal_paths = find_signal_paths(events)
    invalidation_paths = find_invalidation_paths(events)
    guard_paths = find_guard_decision_paths(report.get("decisions", []))
    reconstructed = {
        "event_rows": len(events),
        "observation_rows": sum(row.get("event") == "observation" for row in events),
        "decision_rows": len(report.get("decisions", [])),
        "runtime_signal_rows": len(signal_paths),
        "policy_invalidation_rows": len(invalidation_paths),
        "decisions_with_guard_outcome": len(guard_paths),
    }
    expected = FREEZE["expected"]
    if reconstructed != expected:
        errors.append(f"independent raw reconstruction differs: {reconstructed!r}")
    for key, value in reconstructed.items():
        if result.get(key) != value:
            errors.append(f"candidate {key} differs")
    if result.get("input_sha256") != hashes:
        errors.append("candidate input hashes differ")

    # Confirm the recursive detector notices nested future observations/decisions.
    mutation_controls = [
        len(find_signal_paths({"outer": [{"signal_id": "health", "value": 71}]})) == 1,
        len(find_invalidation_paths({"outer": [{"event": "policy_invalidation"}]})) == 1,
        len(find_guard_decision_paths([{"nested": {"planner_interrupt": {}}}])) == 1,
    ]
    if not all(mutation_controls):
        errors.append("nested-field mutation control failed")

    audit_result = {
        "status": "PASS_AUDIT_V2" if not errors else "FAIL_AUDIT_V2",
        "auditor_sha256": hash_file(Path(__file__)),
        "candidate_sha256": hash_file(PACKAGE / "candidate.py"),
        "auditor_v1_sha256": FREEZE["auditor_sha256"],
        "input_sha256": hashes,
        "reconstructed": reconstructed,
        "signal_paths": signal_paths,
        "invalidation_paths": invalidation_paths,
        "guard_outcome_paths": guard_paths,
        "nested_mutation_controls_passed": sum(mutation_controls),
        "nested_mutation_controls_total": len(mutation_controls),
        "errors": errors,
        "scope": "recursive raw availability audit only; no live controller or gameplay inference",
    }
    destination = PACKAGE / "results" / "audit-v2.json"
    destination.write_text(json.dumps(audit_result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(audit_result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    audit()
