"""Freeze one offline composition of the owner-release evidence path."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = HERE / "FREEZE-A05.json"
PATHS = {
    "lease_cause_v1.py": ROOT / "research/live_control/lease_cause_v1.py",
    "lease_cause_v2.py": ROOT / "research/live_control/lease_cause_v2.py",
    "lease_release_v1.py": ROOT / "research/live_control/lease_release_v1.py",
    "executor_v12.py": ROOT / "research/live_control/executor_v12.py",
    "map01_overlap_controller_v39.py": ROOT / "research/doom/map01_overlap_controller_v39.py",
    "running_action_guard_v3.py": ROOT / "research/live_control/running_action_guard_v3.py",
    "a03_candidate_events.jsonl": HERE / "results/a03/candidate-events.jsonl",
    "a03_result.json": HERE / "results/a03/RESULT.json",
    "run_a05.py": HERE / "run_a05.py",
    "audit_a05.py": HERE / "audit_a05.py",
}


def main():
    if TARGET.exists():
        raise SystemExit("STOP: FREEZE-A05.json already exists")
    sources = {}
    for name, path in PATHS.items():
        raw = path.read_bytes()
        blob = subprocess.check_output(["git", "hash-object", str(path)], cwd=HERE, text=True).strip()
        sources[name] = {"sha256": hashlib.sha256(raw).hexdigest(),
                         "git_blob": blob,
                         "path": path.relative_to(ROOT).as_posix()}
    payload = {
        "run_id": "map01-v39-cancel-cleanup-producer-consumer-a05-20261005",
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip(),
        "python_version": sys.version.split()[0],
        "sources": sources,
        "method": "source-extract current-main lease interruption, executor publication, controller handoff and guard receipt methods; replay retained A03 cleanup",
        "retries": 0,
        "scope": "offline source composition only; not actual process/runtime/game execution",
    }
    TARGET.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(TARGET)


if __name__ == "__main__":
    main()
