"""Frozen WSLc entrypoint; source is read-only and all writes go under /out."""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PACKAGE = Path("/pkg")
OUTPUT = Path("/out")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_hashes():
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    actual = {name: sha256(PACKAGE / name) for name in freeze["sha256"]}
    if actual != freeze["sha256"]:
        raise SystemExit("STOP_FROZEN_SOURCE_HASH_MISMATCH")
    return actual


def main(mode):
    before = frozen_hashes()
    if not OUTPUT.is_dir() or any(OUTPUT.iterdir()):
        raise SystemExit("STOP_OUTPUT_DIRECTORY_NOT_EMPTY")

    if mode == "candidate":
        command = [sys.executable, "-B", "/pkg/candidate.py", "/pkg/input.json", "/out/candidate.jsonl"]
    elif mode == "audit":
        raw = Path("/input/candidate.jsonl")
        if not raw.is_file():
            raise SystemExit("STOP_RETAINED_CANDIDATE_MISSING")
        command = [sys.executable, "-B", "/pkg/auditor.py", "/pkg/input.json", str(raw), "/out/audit.json"]
    else:
        raise SystemExit("usage: run_wslc.py candidate|audit")

    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(command, cwd=str(PACKAGE), env=environment, capture_output=True, text=True)
    (OUTPUT / "stdout.txt").write_text(process.stdout, encoding="utf-8", newline="\n")
    (OUTPUT / "stderr.txt").write_text(process.stderr, encoding="utf-8", newline="\n")
    after = frozen_hashes()
    receipt = {
        "mode": mode,
        "command": command,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "exit_code": process.returncode,
        "frozen_sha256_before": before,
        "frozen_sha256_after": after,
        "frozen_source_unchanged": before == after,
    }
    (OUTPUT / "invocation.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"mode": mode, "exit_code": process.returncode, "source_unchanged": before == after}, sort_keys=True))
    if before != after:
        return 72
    return process.returncode


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: run_wslc.py candidate|audit")
    raise SystemExit(main(sys.argv[1]))
