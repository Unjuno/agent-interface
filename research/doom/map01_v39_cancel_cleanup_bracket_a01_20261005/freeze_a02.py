"""Freeze the one-shot A02 runner, auditor, and owner source."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "FREEZE-A02.json"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=HERE, text=True).strip()


def main():
    if TARGET.exists():
        raise SystemExit("STOP: FREEZE-A02.json already exists")
    paths = ["input_owner_v13.py", "run.py", "audit.py"]
    sources = {}
    for name in paths:
        path = HERE / name
        raw = path.read_bytes()
        sources[name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "git_blob": git("hash-object", str(path)),
        }
    payload = {
        "run_id": "map01-v39-cancel-cleanup-bracket-a02-20261005",
        "base_commit": git("rev-parse", "HEAD"),
        "sources": sources,
        "protocol_change": "A01 candidate/auditor hash mismatch fixed by hashing exact written bytes",
        "method": "offline fake X display; one two-key cancellation cleanup",
        "retries": 0,
    }
    TARGET.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(TARGET)


if __name__ == "__main__":
    main()
