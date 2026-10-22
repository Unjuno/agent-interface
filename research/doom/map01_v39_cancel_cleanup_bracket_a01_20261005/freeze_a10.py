"""Freeze an audit-only replay of retained A03 cancellation raw bytes."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    paths = {
        "events": HERE / "results/a03/candidate-events.jsonl",
        "result": HERE / "results/a03/RESULT.json",
        "freeze_a03": HERE / "FREEZE-A03.json",
        "audit_a03": HERE / "audit_a03.py",
        "auditor": HERE / "audit_a10.py",
        "test": HERE / "test_a10.py",
    }
    sources = {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in paths.items()}
    root = HERE.parents[2]
    value = {
        "schema": "map01-v39-cancel-cleanup-audit-freeze-a10",
        "run_id": "map01-v39-cancel-cleanup-audit-a10-20261005",
        "base_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        "python_version": sys.version.split()[0],
        "sources": sources,
        "candidate_invocations": 0,
        "allocation_reruns": 0,
        "method": "raw-only audit and in-memory mutation controls over retained fake-display A03 candidate bytes",
        "scope": "sample states, sample intervals and request/XSync bracket consistency; no live input, application effect, or game claim",
    }
    target = HERE / "FREEZE-A10.json"
    if target.exists():
        raise SystemExit("STOP: FREEZE-A10.json already exists")
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    print(json.dumps({"path": str(target), "source_count": len(sources),
                      "base_commit": value["base_commit"]}, sort_keys=True))


if __name__ == "__main__":
    main()
