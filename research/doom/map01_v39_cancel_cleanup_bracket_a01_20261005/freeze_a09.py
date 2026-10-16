"""Freeze one offline event transport composition using current source."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = HERE / "FREEZE-A09.json"
PATHS = {
    "session_map01_v12.py": ROOT / "research/doom/session_map01_v12.py",
    "map01_overlap_controller_v39.py": ROOT / "research/doom/map01_overlap_controller_v39.py",
    "a08_published_event.jsonl": HERE / "results/a08/published-events.jsonl",
    "run_a09.py": HERE / "run_a09.py",
    "audit_a09.py": HERE / "audit_a09.py",
}


def main():
    if TARGET.exists():
        raise SystemExit("STOP: FREEZE-A09.json already exists")
    sources = {}
    for name, path in PATHS.items():
        raw = path.read_bytes()
        blob = subprocess.check_output(["git", "hash-object", str(path)], cwd=HERE, text=True).strip()
        sources[name] = {"sha256": hashlib.sha256(raw).hexdigest(),
                         "git_blob": blob,
                         "path": path.relative_to(ROOT).as_posix()}
    payload = {
        "run_id": "map01-v39-cancel-cleanup-jsonl-transport-a09-20261005",
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip(),
        "python_version": sys.version.split()[0],
        "sources": sources,
        "method": "source-extract exact V12 session emit and V39 controller reader/wait; pass retained A08 release event through in-memory pipes",
        "retries": 0,
        "scope": "offline JSONL writer/reader composition only; session main and OS/game runtime are not invoked",
    }
    TARGET.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(TARGET)


if __name__ == "__main__":
    main()
