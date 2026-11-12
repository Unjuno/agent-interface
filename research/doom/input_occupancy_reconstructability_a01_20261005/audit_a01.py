"""Independent raw verification for the retained occupancy evidence census."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results/a01"
RUNS = ("map01-v38-integrated-threat-live-01", "map01-v39-coast-liveness-live-01")


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main():
    errors = []
    freeze = json.loads((HERE / "FREEZE-A01.json").read_text(encoding="utf-8"))
    paths = {"analysis.json": ROOT / "research/doom/results/map01-v38-v39-control-tempo-posthoc-v1/analysis.json",
             "analyze_source.py": ROOT / "research/doom/analyze_map01_v38_v39_control_tempo_posthoc_v1.py",
             "audit_source.py": ROOT / "research/doom/audit_map01_v38_v39_control_tempo_posthoc_v1.py",
             "candidate.py": HERE / "analyze_a01.py", "auditor.py": HERE / "audit_a01.py"}
    for run in RUNS:
        base = ROOT / "research/doom/results" / run
        paths[f"{run}_report.json"] = base / "report.json"
        paths[f"{run}_events.jsonl"] = base / "runtime/events.jsonl"
        paths[f"{run}_owner_events.json"] = base / "runtime/owner-events.json"
    for name, expected in freeze["sources"].items():
        if hashlib.sha256(paths[name].read_bytes()).hexdigest() != expected["sha256"]:
            errors.append(f"frozen source mismatch: {name}")
    result = json.loads((OUT / "RESULT.json").read_text(encoding="utf-8"))
    by_run = {row["run"]: row for row in result["runs"]}
    for run in RUNS:
        event_rows = rows(paths[f"{run}_events.jsonl"])
        owner = json.loads(paths[f"{run}_owner_events.json"].read_text(encoding="utf-8"))
        current = by_run[run]
        counts = Counter(row.get("event") for row in event_rows)
        admissions = [row for row in event_rows if row.get("event") == "input_admission"]
        releases = [row for row in event_rows if row.get("event") in ("input_release_measurement", "input_released")]
        if current["input_admission_count"] != counts.get("input_admission", 0):
            errors.append(f"{run}: admission count mismatch")
        if current["keys_held_snapshot_count"] != counts.get("keys_held", 0):
            errors.append(f"{run}: held snapshot count mismatch")
        if current["input_release_measurement_or_published_release_count"] != len(releases):
            errors.append(f"{run}: release event count mismatch")
        if current["admissions_with_program_id_and_step"] != sum(
                type(row.get("id")) is str and type(row.get("step")) is int for row in admissions):
            errors.append(f"{run}: admission correlation count mismatch")
        owner_per_key = sum(len(row.get("per_key_release_measurements", [])) for row in owner if type(row) is dict)
        if current["per_key_up_measurements_in_owner_event_ledger"] != owner_per_key:
            errors.append(f"{run}: owner per-key release count mismatch")
        if current["exact_per_key_occupancy_reconstructable"]:
            errors.append(f"{run}: result overclaims exact physical occupancy")
        if current["all_terminals_verified_empty"] is not True:
            errors.append(f"{run}: aggregate terminal cleanup result mismatch")
    if result.get("status") != "FAIL_INSUFFICIENT_PER_KEY_EDGE_EVIDENCE":
        errors.append("expected insufficient-evidence disposition")
    audit = {"run_id": freeze["run_id"],
             "disposition": "PASS_AUDITED_INSUFFICIENT_EVIDENCE" if not errors else "FAIL_MISMATCH",
             "run_count": len(RUNS), "errors": errors,
             "scope": "audits the negative evidence-sufficiency conclusion; not a claim about physical safety or failure"}
    (OUT / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8", newline="\n")
    print(json.dumps(audit, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
