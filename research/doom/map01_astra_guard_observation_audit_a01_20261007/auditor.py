import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit():
    errors = []
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != FREEZE["auditor_sha256"]:
        errors.append("auditor source hash differs")
    candidate_path = PACKAGE / "candidate.py"
    if hashlib.sha256(candidate_path.read_bytes()).hexdigest() != FREEZE["candidate_sha256"]:
        errors.append("candidate source hash differs")
    event_path = ROOT / "research/doom/results/map01-astra-attempt-v1/events.jsonl"
    report_path = ROOT / "research/doom/results/map01-astra-attempt-v1/report.json"
    event_bytes = event_path.read_bytes()
    report_bytes = report_path.read_bytes()
    hashes = {
        str(event_path.relative_to(ROOT)).replace("\\", "/"):
            hashlib.sha256(event_bytes).hexdigest(),
        str(report_path.relative_to(ROOT)).replace("\\", "/"):
            hashlib.sha256(report_bytes).hexdigest(),
    }
    if hashes != FREEZE["inputs"]:
        errors.append("frozen input hashes differ")

    event_rows = [json.loads(line) for line in event_bytes.splitlines()]
    report = json.loads(report_bytes)
    observation_rows = [row for row in event_rows
                        if row.get("event") == "observation"]
    signal_rows = []
    invalidation_rows = []
    for index, row in enumerate(event_rows):
        if row.get("event") in ("health_signal", "ammo_signal"):
            signal_rows.append(index)
        if row.get("event") in ("policy_invalidation", "running_action_invalidation"):
            invalidation_rows.append(index)
        signal_id = row.get("signal_id")
        if signal_id in ("health", "ammo") and "value" in row:
            signal_rows.append(index)
    decision_rows = report.get("decisions", [])
    guarded = [i for i, row in enumerate(decision_rows)
               if any(key in row for key in (
                   "policy_invalidation", "cover_validity_admission",
                   "cover_validity_soft_events", "planner_interrupt"))]
    reconstructed = {
        "event_rows": len(event_rows),
        "observation_rows": len(observation_rows),
        "decision_rows": len(decision_rows),
        "runtime_signal_rows": len(set(signal_rows)),
        "policy_invalidation_rows": len(set(invalidation_rows)),
        "decisions_with_guard_outcome": len(guarded),
    }
    if reconstructed != FREEZE["expected"]:
        errors.append(f"independent counts differ: {reconstructed!r}")

    result = load_json(PACKAGE / "results" / "a01.json")
    if result.get("input_sha256") != hashes:
        errors.append("candidate input hashes differ")
    for key, value in reconstructed.items():
        if result.get(key) != value:
            errors.append(f"candidate {key} differs from independent count")
    if result.get("status") != "PASS_OBSERVABILITY_GAP_ONLY":
        errors.append("candidate status is not scoped pass")

    audit_result = {
        "status": "PASS_AUDIT" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "reconstructed": reconstructed,
        "input_sha256": hashes,
        "scope": "independent raw availability reconstruction only",
    }
    out = PACKAGE / "results" / "audit-a01.json"
    out.write_text(json.dumps(audit_result, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps(audit_result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    audit()
