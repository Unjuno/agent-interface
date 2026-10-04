"""Independently check the retained timestamp-detachment run artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
FIXTURE = PACKAGE / "00-coast"
MUTATED = HERE / "mutated" / "sample-pair-04" / "00-coast"
RUN = json.loads((HERE / "RUN.json").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


original_events = read_jsonl(FIXTURE / "events.jsonl")
mutated_events = read_jsonl(MUTATED / "events.jsonl")
capture_ns = next(
    event["capture_ns"]
    for event in original_events
    if event.get("event") == "typed_observation" and event.get("id") == "initial"
)
coherent = [row for row in read_jsonl(MUTATED / "scorer-last-action.jsonl") if row.get("coherent_tic")]
has_sample_before = any(row["sample_returned_ns"] <= capture_ns for row in coherent)
has_sample_after = any(row["sample_started_ns"] >= capture_ns for row in coherent)
source_hashes = {
    name: sha256(FIXTURE / name)
    for name in ("RESULT.json", "FINAL.json", "events.jsonl", "scorer-last-action.jsonl")
}
mutated_hashes = {
    name: sha256(MUTATED / name)
    for name in ("RESULT.json", "FINAL.json", "events.jsonl", "scorer-last-action.jsonl")
}
checks = {
    "retained_input_hashes_match_run_record": source_hashes == RUN["input_sha256"],
    "mutated_input_hashes_match_run_record": mutated_hashes == RUN["mutated_input_sha256"],
    "frozen_baseline_bytes_match_run_record": sha256(HERE / "baseline_auditor.py") == RUN["baseline_source_sha256"],
    "ordinary_event_stream_unchanged": original_events == mutated_events,
    "baseline_false_pass_reproduced": RUN["baseline_report"]["disposition"] == "PASS_HUD_WEAPON_AMMO_BINDING_SCOPED",
    "candidate_rejects_timestamp_detachment": RUN["candidate_report"]["disposition"] == "HOLD_AUDIT_CHECK_FAILED",
    "candidate_reports_missing_api_bracket": RUN["candidate_report"]["checks"].get("api_timeline_brackets_hud_capture") is False,
    "mutated_samples_have_no_before_bracket": not has_sample_before,
    "mutated_samples_have_after_side": has_sample_after,
    "retained_fixture_files_unmodified_by_run": all(
        RUN["input_sha256"][name] == sha256(FIXTURE / name)
        for name in ("RESULT.json", "FINAL.json", "events.jsonl", "scorer-last-action.jsonl")
    ),
}
report = {
    "experiment_id": RUN["experiment_id"],
    "independent_audit": "PASS_MUTATION_REJECTED" if all(checks.values()) else "FAIL_AUDIT",
    "checks": checks,
    "typed_hud_capture_ns": capture_ns,
    "mutated_coherent_sample_count": len(coherent),
    "mutated_sample_before_capture_exists": has_sample_before,
    "mutated_sample_after_capture_exists": has_sample_after,
    "baseline_nearest_offset_ns": RUN["baseline_report"].get("nearest_api_offset_ns"),
    "candidate_nearest_offset_ns": RUN["candidate_report"].get("nearest_api_offset_ns"),
}
(HERE / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
