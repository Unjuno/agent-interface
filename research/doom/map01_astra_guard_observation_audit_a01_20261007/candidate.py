import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(value, path="$"):
    if isinstance(value, dict):
        yield path, value
        for key, item in value.items():
            yield from walk(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk(item, f"{path}[{index}]")


def run():
    if sha256(Path(__file__)) != FREEZE["candidate_sha256"]:
        raise SystemExit("FAIL_CANDIDATE_SOURCE_HASH")
    if sha256(PACKAGE / "auditor.py") != FREEZE["auditor_sha256"]:
        raise SystemExit("FAIL_AUDITOR_SOURCE_HASH")
    inputs = {name: ROOT / name for name in FREEZE["inputs"]}
    actual_hashes = {name: sha256(path) for name, path in inputs.items()}
    if actual_hashes != FREEZE["inputs"]:
        raise SystemExit("FAIL_INPUT_HASH_MISMATCH")

    events = [json.loads(line) for line in inputs[
        "research/doom/results/map01-astra-attempt-v1/events.jsonl"
    ].read_text(encoding="utf-8").splitlines()]
    report = json.loads(inputs[
        "research/doom/results/map01-astra-attempt-v1/report.json"
    ].read_text(encoding="utf-8"))
    observations = [row for row in events if row.get("event") == "observation"]

    signal_rows = []
    invalidation_rows = []
    for index, row in enumerate(events):
        for path, obj in walk(row, f"events[{index}]"):
            event = obj.get("event")
            if event in ("health_signal", "ammo_signal", "policy_invalidation",
                         "running_action_invalidation"):
                if event in ("health_signal", "ammo_signal"):
                    signal_rows.append(path)
                else:
                    invalidation_rows.append(path)
            signal_id = obj.get("signal_id")
            if signal_id in ("health", "ammo") and "value" in obj:
                signal_rows.append(path)

    guard_outcomes = []
    for index, decision in enumerate(report.get("decisions", [])):
        for path, obj in walk(decision, f"decisions[{index}]"):
            if any(key in obj for key in (
                    "policy_invalidation", "cover_validity_admission",
                    "cover_validity_soft_events", "planner_interrupt")):
                guard_outcomes.append(path)

    result = {
        "status": "PASS_OBSERVABILITY_GAP_ONLY",
        "input_sha256": actual_hashes,
        "event_rows": len(events),
        "observation_rows": len(observations),
        "decision_rows": len(report.get("decisions", [])),
        "runtime_signal_rows": len(set(signal_rows)),
        "runtime_signal_paths": sorted(set(signal_rows)),
        "policy_invalidation_rows": len(set(invalidation_rows)),
        "policy_invalidation_paths": sorted(set(invalidation_rows)),
        "decisions_with_guard_outcome": len(set(guard_outcomes)),
        "guard_outcome_paths": sorted(set(guard_outcomes)),
        "scope": FREEZE["scope"],
    }
    expected = FREEZE["expected"]
    for key, value in expected.items():
        if result.get(key) != value:
            result["status"] = "FAIL_EXPECTED_FIELD_MISMATCH"
            result.setdefault("errors", []).append(
                f"{key}: expected {value!r}, got {result.get(key)!r}")

    destination = PACKAGE / "results" / "a01.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_OBSERVABILITY_GAP_ONLY":
        raise SystemExit(1)


if __name__ == "__main__":
    run()
