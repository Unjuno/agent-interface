"""Freeze retained inputs for a no-rerun physical occupancy audit."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = HERE / "FREEZE-A01.json"
RUNS = ("map01-v38-integrated-threat-live-01", "map01-v39-coast-liveness-live-01")
PATHS = {"analysis.json": ROOT / "research/doom/results/map01-v38-v39-control-tempo-posthoc-v1/analysis.json",
         "analyze_source.py": ROOT / "research/doom/analyze_map01_v38_v39_control_tempo_posthoc_v1.py",
         "audit_source.py": ROOT / "research/doom/audit_map01_v38_v39_control_tempo_posthoc_v1.py",
         "candidate.py": HERE / "analyze_a01.py",
         "auditor.py": HERE / "audit_a01.py"}
for run in RUNS:
    PATHS[f"{run}_report.json"] = ROOT / "research/doom/results" / run / "report.json"
    PATHS[f"{run}_events.jsonl"] = ROOT / "research/doom/results" / run / "runtime/events.jsonl"
    PATHS[f"{run}_owner_events.json"] = ROOT / "research/doom/results" / run / "runtime/owner-events.json"


def main():
    if TARGET.exists():
        raise SystemExit("STOP: FREEZE-A01.json already exists")
    sources = {}
    for name, path in PATHS.items():
        raw = path.read_bytes()
        blob = subprocess.check_output(["git", "hash-object", str(path)], cwd=HERE, text=True).strip()
        sources[name] = {"sha256": hashlib.sha256(raw).hexdigest(),
                         "git_blob": blob, "path": path.relative_to(ROOT).as_posix()}
    value = {"run_id": "map01-held-input-reconstructability-a01-20261005",
             "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip(),
             "python_version": sys.version.split()[0], "sources": sources,
             "method": "read-only event-schema census and cross-file consistency audit; no retained allocation reruns",
             "retries": 0,
             "scope": "whether retained v38/v39 outputs can reconstruct per-key physical held occupancy"}
    TARGET.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(TARGET)


if __name__ == "__main__":
    main()
