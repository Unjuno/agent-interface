#!/usr/bin/env python3
"""Run the frozen PR #8290 regression suite against base and candidate blobs."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time


BASE = "9fb2dd6782d1d1477a00d14be870487fd4c54fa2"
CANDIDATE = "c6f5a122afee85e44bec5c39b80f02e6b939d56a"
SOURCE_PATH = "research/live_control/codex_app_server_client_v2.py"
TEST_PATH = "research/live_control/test_appserver_process_tree_cleanup_20261004.py"
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"


def git_blob(commit: str, path: str) -> tuple[bytes, str]:
    data = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
    blob = subprocess.check_output(
        ["git", "rev-parse", f"{commit}:{path}"], cwd=ROOT, text=True
    ).strip()
    return data, blob


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_one(label: str, commit: str, test_data: bytes, test_blob: str) -> dict:
    source, source_blob = git_blob(commit, SOURCE_PATH)
    with tempfile.TemporaryDirectory(prefix=f"eof-reap-{label}-") as tmp:
        tmp_path = Path(tmp)
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        source_file = source_dir / Path(SOURCE_PATH).name
        source_file.write_bytes(source)
        test_file = tmp_path / "frozen_test.py"
        test_file.write_bytes(test_data)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(source_dir)
        command = [sys.executable, "-B", str(test_file), "-v"]
        started = time.monotonic()
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=45,
            check=False,
        )
        elapsed = time.monotonic() - started

    log_path = RAW / f"{label}.txt"
    log_path.write_text(completed.stdout, encoding="utf-8")
    return {
        "label": label,
        "commit": commit,
        "source_path": SOURCE_PATH,
        "source_git_blob": source_blob,
        "source_sha256": sha256(source),
        "test_source_commit": CANDIDATE,
        "test_path": TEST_PATH,
        "test_git_blob": test_blob,
        "test_sha256": sha256(test_data),
        "command": command,
        "cwd": "repository root",
        "python": sys.version,
        "platform": platform.platform(),
        "elapsed_seconds": round(elapsed, 6),
        "exit_code": completed.returncode,
        "raw_log": str(log_path.relative_to(HERE)),
        "raw_log_sha256": sha256(completed.stdout.encode("utf-8")),
    }


def main() -> int:
    RAW.mkdir(exist_ok=True)
    test_data, test_blob = git_blob(CANDIDATE, TEST_PATH)
    (HERE / "frozen_test.py").write_bytes(test_data)
    results = [
        run_one("base", BASE, test_data, test_blob),
        run_one("candidate", CANDIDATE, test_data, test_blob),
    ]
    result = {
        "format": "appserver-eof-reap-independent-recheck-v1",
        "base": BASE,
        "candidate": CANDIDATE,
        "test_commit": CANDIDATE,
        "runs": results,
        "disposition": "PASS_REPAIR_RECHECK" if results[1]["exit_code"] == 0 else "FAIL",
        "scope": "same frozen eight-case regression suite, same host and runtime, base versus PR candidate",
    }
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for row in results:
        print(f"{row['label']}: exit={row['exit_code']} log={row['raw_log']}")
    print(f"disposition={result['disposition']}")
    return 0 if result["disposition"] == "PASS_REPAIR_RECHECK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
