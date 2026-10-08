"""Generate a source-bound freeze once, before the candidate is run."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "input_owner_v13.py"
TARGET = HERE / "FREEZE.json"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=HERE, text=True).strip()


def main():
    if TARGET.exists():
        raise SystemExit("STOP: FREEZE.json already exists")
    raw = SOURCE.read_bytes()
    payload = {
        "run_id": "map01-v39-cancel-cleanup-bracket-a01-20261005",
        "base_commit": git("rev-parse", "HEAD"),
        "source": {
            "path": SOURCE.relative_to(HERE.parents[2]).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "git_blob": git("hash-object", str(SOURCE)),
        },
        "method": "offline fake X display; one two-key cancellation cleanup",
        "retries": 0,
    }
    TARGET.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(TARGET)


if __name__ == "__main__":
    main()
