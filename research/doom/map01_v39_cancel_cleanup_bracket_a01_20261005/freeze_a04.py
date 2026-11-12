"""Freeze one source-extracted release receipt flow replay."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = HERE / "FREEZE-A04.json"
PATHS = {
    "running_action_guard_v3.py": ROOT / "research" / "live_control" / "running_action_guard_v3.py",
    "a03_candidate_events.jsonl": HERE / "results" / "a03" / "candidate-events.jsonl",
    "run_a04.py": HERE / "run_a04.py",
    "audit_a04.py": HERE / "audit_a04.py",
}


def main():
    if TARGET.exists():
        raise SystemExit("STOP: FREEZE-A04.json already exists")
    sources = {}
    for name, path in PATHS.items():
        raw = path.read_bytes()
        blob = subprocess.check_output(["git", "hash-object", str(path)], cwd=HERE, text=True).strip()
        sources[name] = {"sha256": hashlib.sha256(raw).hexdigest(),
                         "git_blob": blob,
                         "path": path.relative_to(ROOT).as_posix()}
    payload = {"run_id": "map01-v39-cancel-cleanup-receipt-flow-a04-20261005",
               "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip(),
               "python_version": sys.version.split()[0],
               "sources": sources,
               "method": "source-extract RunningActionGuardV3.record_input_released; replay retained A03 fake-display owner_release",
               "retries": 0}
    TARGET.write_text(json.dumps(payload, indent=2) + "\n")
    print(TARGET)


if __name__ == "__main__":
    main()
