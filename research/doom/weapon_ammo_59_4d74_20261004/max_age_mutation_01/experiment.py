"""Run the frozen timestamp-detachment mutation against baseline and candidate auditors."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
FIXTURE = PACKAGE / "00-coast"
MUTATED_ROOT = HERE / "mutated"
MUTATED = MUTATED_ROOT / "sample-pair-04" / "00-coast"
BASELINE = HERE / "baseline_auditor.py"
CANDIDATE = PACKAGE / "audit_weapon_ammo_followup_02.py"
OFFSET_NS = 1_000_000_000_000
EXPERIMENT_ID = "weapon-ammo-api-timeline-bracket-01"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load auditor: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def main() -> int:
    shutil.rmtree(MUTATED_ROOT, ignore_errors=True)
    MUTATED.mkdir(parents=True)
    for name in ("RESULT.json", "FINAL.json", "events.jsonl", "scorer-last-action.jsonl"):
        shutil.copyfile(FIXTURE / name, MUTATED / name)

    result_path = MUTATED / "RESULT.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["window_start_ns"] += OFFSET_NS
    result["window_end_ns"] += OFFSET_NS
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    rows_path = MUTATED / "scorer-last-action.jsonl"
    rows = read_jsonl(rows_path)
    for row in rows:
        if row.get("coherent_tic"):
            row["sample_started_ns"] += OFFSET_NS
            row["sample_returned_ns"] += OFFSET_NS
    events = read_jsonl(MUTATED / "events.jsonl")
    initial = next(
        event
        for event in events
        if event.get("event") == "typed_observation" and event.get("id") == "initial"
    )
    nearest = min(
        (row for row in rows if row.get("coherent_tic")),
        key=lambda row: abs(row["sample_returned_ns"] - initial["capture_ns"]),
    )
    nearest["variables"].update(
        HEALTH=97.0,
        SELECTED_WEAPON=2.0,
        SELECTED_WEAPON_AMMO=48.0,
        AMMO2=48.0,
    )
    write_jsonl(rows_path, rows)

    baseline = load_module("baseline_auditor", BASELINE)
    candidate = load_module("candidate_auditor", CANDIDATE)
    baseline_report = baseline.audit(MUTATED_ROOT)
    candidate_report = candidate.audit(MUTATED_ROOT)
    coherent = [row for row in rows if row.get("coherent_tic")]
    out = {
        "experiment_id": EXPERIMENT_ID,
        "command": "python experiment.py; python audit.py",
        "execution": {
            "platform": platform.platform(),
            "python": sys.version,
            "worktree_head_before_change": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=PACKAGE, text=True
            ).strip(),
        },
        "baseline_commit": "bb87895fa6103575e929fcd8e3d61a62fa96740c",
        "baseline_git_blob": "4a0707abecdf7323ed49692014c688b0f8a4cd4e",
        "baseline_source_sha256": sha256(BASELINE),
        "candidate_worktree_base": "bb87895fa6103575e929fcd8e3d61a62fa96740c",
        "candidate_source_sha256": sha256(CANDIDATE),
        "experiment_source_sha256": sha256(Path(__file__).resolve()),
        "independent_auditor_source_sha256": sha256(HERE / "audit.py"),
        "freeze_sha256": sha256(HERE / "FREEZE.json"),
        "input_sha256": {
            name: sha256(FIXTURE / name)
            for name in ("RESULT.json", "FINAL.json", "events.jsonl", "scorer-last-action.jsonl")
        },
        "mutated_input_sha256": {
            name: sha256(MUTATED / name)
            for name in ("RESULT.json", "FINAL.json", "events.jsonl", "scorer-last-action.jsonl")
        },
        "mutation": {
            "coherent_rows_shifted": len(coherent),
            "timestamp_offset_ns": OFFSET_NS,
            "nearest_sample_offset_from_hud_ns": min(
                abs(row["sample_returned_ns"] - initial["capture_ns"]) for row in coherent
            ),
            "nearest_sample_fields_aligned_to_hud": ["HEALTH", "SELECTED_WEAPON", "SELECTED_WEAPON_AMMO", "AMMO2"],
        },
        "baseline_report": baseline_report,
        "candidate_report": candidate_report,
    }
    (HERE / "RUN.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
