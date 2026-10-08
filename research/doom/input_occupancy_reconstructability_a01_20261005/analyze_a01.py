"""Measure whether retained v38/v39 event logs contain exact per-key occupancy evidence."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = HERE / "FREEZE-A01.json"
OUT = HERE / "results/a01"
RUNS = ("map01-v38-integrated-threat-live-01", "map01-v39-coast-liveness-live-01")


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main():
    if OUT.exists():
        raise SystemExit("STOP: A01 candidate output already exists")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    paths = {"analysis.json": ROOT / "research/doom/results/map01-v38-v39-control-tempo-posthoc-v1/analysis.json",
             "analyze_source.py": ROOT / "research/doom/analyze_map01_v38_v39_control_tempo_posthoc_v1.py",
             "audit_source.py": ROOT / "research/doom/audit_map01_v38_v39_control_tempo_posthoc_v1.py",
             "candidate.py": HERE / "analyze_a01.py", "auditor.py": HERE / "audit_a01.py"}
    for run in RUNS:
        paths[f"{run}_report.json"] = ROOT / "research/doom/results" / run / "report.json"
        paths[f"{run}_events.jsonl"] = ROOT / "research/doom/results" / run / "runtime/events.jsonl"
        paths[f"{run}_owner_events.json"] = ROOT / "research/doom/results" / run / "runtime/owner-events.json"
    for name, record in freeze["sources"].items():
        if hashlib.sha256(paths[name].read_bytes()).hexdigest() != record["sha256"]:
            raise SystemExit(f"STOP: frozen source mismatch: {name}")
    if sys.version.split()[0] != freeze["python_version"]:
        raise SystemExit("STOP: Python runtime mismatch")

    results = []
    for run in RUNS:
        run_root = ROOT / "research/doom/results" / run
        report = json.loads((run_root / "report.json").read_text(encoding="utf-8"))
        events = load_jsonl(run_root / "runtime/events.jsonl")
        owner_events = json.loads((run_root / "runtime/owner-events.json").read_text(encoding="utf-8"))
        counts = Counter(row.get("event") for row in events)
        admissions = [row for row in events if row.get("event") == "input_admission"]
        held_snapshots = [row for row in events if row.get("event") == "keys_held"]
        releases = [row for row in events if row.get("event") in ("input_release_measurement", "input_released")]
        down_actuation_ids = [row.get("physical_key_measurement", {}).get("actuation_id")
                              for row in admissions if type(row.get("physical_key_measurement")) is dict]
        up_actuation_ids = [row.get("physical_key_measurement", {}).get("actuation_id")
                            for row in releases if type(row.get("physical_key_measurement")) is dict]
        owner_per_key = sum(len(row.get("per_key_release_measurements", []))
                            for row in owner_events if type(row) is dict)
        event_per_key = sum(len(row.get("owner_release", {}).get("per_key_release_measurements", []))
                            for row in releases if type(row.get("owner_release")) is dict)
        hold_steps = sum(1 for decision in report["decisions"] for program in decision.get("programs", [])
                         for step in program.get("steps", []) if type(step) is dict and step.get("op") == "hold")
        results.append({
            "run": run,
            "report_decision_count": len(report["decisions"]),
            "event_type_counts": dict(sorted(counts.items())),
            "input_admission_count": len(admissions),
            "admissions_with_program_id_and_step": sum(type(row.get("id")) is str and type(row.get("step")) is int
                                                        for row in admissions),
            "admissions_with_physical_down_interval_and_actuation_id": sum(
                type(row.get("physical_key_measurement", {}).get("bracket")) is dict and
                type(row["physical_key_measurement"].get("actuation_id")) is str and
                row["physical_key_measurement"]["bracket"].get("physical_down_interval") is not None
                for row in admissions if type(row.get("physical_key_measurement")) is dict),
            "keys_held_snapshot_count": len(held_snapshots),
            "input_release_measurement_or_published_release_count": len(releases),
            "release_events_with_program_id_and_step": sum(type(row.get("id")) is str and type(row.get("step")) is int
                                                             for row in releases),
            "per_key_up_measurements_in_event_release_payloads": event_per_key,
            "per_key_up_measurements_in_owner_event_ledger": owner_per_key,
            "down_actuation_ids": down_actuation_ids,
            "up_actuation_ids": up_actuation_ids,
            "terminal_count": counts.get("terminal", 0),
            "all_terminals_verified_empty": all(row.get("release", {}).get("verified") is True and
                                                  row.get("release", {}).get("keys_down") == []
                                                  for row in events if row.get("event") == "terminal"),
            "exact_per_key_occupancy_reconstructable": bool(admissions) and
                len(down_actuation_ids) == len(admissions) and len(up_actuation_ids) >= len(admissions) and
                set(down_actuation_ids) <= set(up_actuation_ids),
        })
    decision = "PASS_EXACT_PER_KEY_OCCUPANCY_AVAILABLE" if all(
        row["exact_per_key_occupancy_reconstructable"] for row in results) else "FAIL_INSUFFICIENT_PER_KEY_EDGE_EVIDENCE"
    OUT.mkdir(parents=True)
    value = {"run_id": freeze["run_id"], "status": decision, "runs": results,
             "scope": "retained log sufficiency only; absence of exact per-key edges does not mean input was stuck or unsafe",
             "next_measurement_minimum": [
                 "correlate each down/up with immutable actuation_id, intent token, program id and step",
                 "retain conservative per-key physical_down_interval and physical_up_interval sample brackets",
                 "retain every ordinary up and emergency cleanup up result; aggregate empty release alone is insufficient",
                 "retain independent first useful task-effect receipt and time with its source frame/program",
             ]}
    raw = json.dumps(value, indent=2, sort_keys=True) + "\n"
    (OUT / "RESULT.json").write_text(raw, encoding="utf-8", newline="\n")
    print(json.dumps({"status": decision, "runs": [
        {"run": row["run"], "input_admission_count": row["input_admission_count"],
         "keys_held_snapshot_count": row["keys_held_snapshot_count"],
         "release_count": row["input_release_measurement_or_published_release_count"],
         "exact_per_key_occupancy_reconstructable": row["exact_per_key_occupancy_reconstructable"]}
        for row in results]}, sort_keys=True))


if __name__ == "__main__":
    main()
