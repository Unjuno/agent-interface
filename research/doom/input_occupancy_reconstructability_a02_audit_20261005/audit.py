"""Recompute every A01 occupancy field from frozen retained records."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUNS = ("map01-v38-integrated-threat-live-01", "map01-v39-coast-liveness-live-01")
RESULT_PATH = (ROOT / "research/doom/input_occupancy_reconstructability_a01_20261005"
               / "results/a01/RESULT.json")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def strict_equal(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(strict_equal(left[key], right[key]) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(strict_equal(a, b) for a, b in zip(left, right))
    return left == right


def derive_run(report, events, owner_events):
    counts = Counter(row.get("event") for row in events)
    admissions = [row for row in events if row.get("event") == "input_admission"]
    held = [row for row in events if row.get("event") == "keys_held"]
    releases = [row for row in events if row.get("event") in ("input_release_measurement", "input_released")]

    down_ids = [row.get("physical_key_measurement", {}).get("actuation_id")
                for row in admissions if type(row.get("physical_key_measurement")) is dict]
    up_ids = [row.get("physical_key_measurement", {}).get("actuation_id")
              for row in releases if type(row.get("physical_key_measurement")) is dict]
    down_receipts = sum(
        type((physical := row.get("physical_key_measurement"))) is dict
        and type((bracket := physical.get("bracket"))) is dict
        and type(physical.get("actuation_id")) is str
        and bracket.get("physical_down_interval") is not None
        for row in admissions
    )

    event_per_key_up = 0
    for row in releases:
        release = row.get("owner_release")
        if type(release) is dict:
            measurements = release.get("per_key_release_measurements", [])
            if type(measurements) is list:
                event_per_key_up += len(measurements)

    owner_per_key_up = sum(
        len(row["per_key_release_measurements"])
        for row in owner_events
        if type(row) is dict and type(row.get("per_key_release_measurements")) is list
    )
    unique_down = all(type(value) is str for value in down_ids) and len(set(down_ids)) == len(down_ids)
    unique_up = all(type(value) is str for value in up_ids) and len(set(up_ids)) == len(up_ids)
    reconstructable = bool(admissions) and down_receipts == len(admissions) and \
        len(down_ids) == len(admissions) and len(up_ids) >= len(admissions) and \
        unique_down and unique_up and set(down_ids) <= set(up_ids)
    terminals = [row for row in events if row.get("event") == "terminal"]

    return {
        "report_decision_count": len(report.get("decisions", [])),
        "event_type_counts": dict(sorted(counts.items())),
        "input_admission_count": len(admissions),
        "admissions_with_program_id_and_step": sum(
            type(row.get("id")) is str and type(row.get("step")) is int for row in admissions),
        "admissions_with_physical_down_interval_and_actuation_id": down_receipts,
        "keys_held_snapshot_count": len(held),
        "input_release_measurement_or_published_release_count": len(releases),
        "release_events_with_program_id_and_step": sum(
            type(row.get("id")) is str and type(row.get("step")) is int for row in releases),
        "per_key_up_measurements_in_event_release_payloads": event_per_key_up,
        "per_key_up_measurements_in_owner_event_ledger": owner_per_key_up,
        "down_actuation_ids": down_ids,
        "up_actuation_ids": up_ids,
        "terminal_count": len(terminals),
        "all_terminals_verified_empty": all(
            row.get("release", {}).get("verified") is True
            and row.get("release", {}).get("keys_down") == [] for row in terminals),
        "exact_per_key_occupancy_reconstructable": reconstructable,
    }


def audit_result(result, evidence):
    """Return mismatches between an A01 result and independently derived raw metrics."""
    errors = []
    rows = result.get("runs")
    if type(rows) is not list:
        return ["runs is not a list"]
    by_run = {}
    for row in rows:
        if type(row) is not dict or type(row.get("run")) is not str or row["run"] in by_run:
            errors.append("run rows are malformed or duplicated")
            continue
        by_run[row["run"]] = row
    if set(by_run) != set(RUNS):
        errors.append("run identity set mismatch")

    expected_status = "PASS_EXACT_PER_KEY_OCCUPANCY_AVAILABLE"
    for run in RUNS:
        current = by_run.get(run)
        raw = evidence.get(run)
        if current is None or type(raw) is not dict or not all(
                key in raw for key in ("report", "events", "owner_events")):
            errors.append(f"{run}: missing result or raw evidence")
            continue
        derived = derive_run(raw["report"], raw["events"], raw["owner_events"])
        for name, actual in derived.items():
            observed = current.get(name)
            if not strict_equal(observed, actual):
                errors.append(f"{run}: {name} does not match frozen raw records")
        if not derived["exact_per_key_occupancy_reconstructable"]:
            expected_status = "FAIL_INSUFFICIENT_PER_KEY_EDGE_EVIDENCE"
    if result.get("status") != expected_status:
        errors.append("overall status does not follow raw per-key evidence")
    return errors


def load_frozen_inputs():
    freeze_path = HERE / "FREEZE-A02.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    paths = {
        "a01_result": RESULT_PATH,
        "a01_freeze": ROOT / "research/doom/input_occupancy_reconstructability_a01_20261005/FREEZE-A01.json",
        "a01_freeze_script": ROOT / "research/doom/input_occupancy_reconstructability_a01_20261005/freeze_a01.py",
        "a01_manifest": ROOT / "research/doom/input_occupancy_reconstructability_a01_20261005/SHA256SUMS",
        "a01_candidate": ROOT / "research/doom/input_occupancy_reconstructability_a01_20261005/analyze_a01.py",
        "a01_auditor": ROOT / "research/doom/input_occupancy_reconstructability_a01_20261005/audit_a01.py",
        "a02_readme": HERE / "README.md",
        "a02_mutation_note": HERE / "BASELINE_MUTATION.md",
        "a02_auditor": HERE / "audit.py",
        "a02_tests": HERE / "test_audit.py",
    }
    evidence = {}
    for run in RUNS:
        base = ROOT / "research/doom/results" / run
        report = base / "report.json"
        events = base / "runtime/events.jsonl"
        owner = base / "runtime/owner-events.json"
        paths[f"{run}_report"] = report
        paths[f"{run}_events"] = events
        paths[f"{run}_owner_events"] = owner
        evidence[run] = {
            "report": json.loads(report.read_text(encoding="utf-8")),
            "events": read_jsonl(events),
            "owner_events": json.loads(owner.read_text(encoding="utf-8")),
        }
    for name, expected in freeze["sources"].items():
        actual = hashlib.sha256(paths[name].read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"frozen source hash mismatch: {name}")
    return freeze, json.loads(RESULT_PATH.read_text(encoding="utf-8")), evidence


def main():
    freeze, result, evidence = load_frozen_inputs()
    errors = audit_result(result, evidence)
    summaries = {run: derive_run(raw["report"], raw["events"], raw["owner_events"])
                 for run, raw in evidence.items()}
    report = {
        "schema": "map01-per-key-occupancy-a02-audit-v1",
        "run_id": freeze["run_id"],
        "source_main": freeze["source_main"],
        "a01_head": freeze["a01_head"],
        "a01_result_sha256": hashlib.sha256(RESULT_PATH.read_bytes()).hexdigest(),
        "result_status": result.get("status"),
        "run_count": len(result.get("runs", [])),
        "recomputed": summaries,
        "errors": errors,
        "decision": "PASS_RAW_DERIVED_AUDIT" if not errors else "FAIL_AUDIT_MISMATCH",
        "scope": "independent metric-to-raw consistency only; no allocation or physical effect claim",
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
