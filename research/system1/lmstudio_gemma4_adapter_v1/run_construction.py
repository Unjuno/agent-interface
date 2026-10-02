"""Run one host-only LM Studio adapter contract suite and retain raw output."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEFAULT_OUTPUT = HERE / "results" / "construction-01" / "runner.json"
SOURCE_FILES = (
    "README.md",
    "lmstudio_chat.py",
    "test_lmstudio_chat.py",
    "run_construction.py",
    "audit_construction.py",
)
TEST_PATH = "research/system1/lmstudio_gemma4_adapter_v1/test_lmstudio_chat.py"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")
    if not output.is_relative_to(HERE):
        raise SystemExit("output must remain under this evidence directory")
    missing = [name for name in SOURCE_FILES if not (HERE / name).is_file()]
    if missing:
        raise SystemExit(f"missing frozen source file(s): {missing}")

    command = [sys.executable, "-m", "pytest", "-q", TEST_PATH]
    started = datetime.now(timezone.utc).isoformat()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        returncode = None
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        timed_out = True

    match = re.search(r"\b(\d+) passed\b", stdout)
    report = {
        "experiment": "lmstudio_gemma4_adapter_v1_construction",
        "status": "TIMEOUT" if timed_out else ("PASS" if returncode == 0 else "FAIL"),
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "host_platform": platform.platform(),
        "python_version": platform.python_version(),
        "command_display": f"python -m pytest -q {TEST_PATH}",
        "returncode": returncode,
        "test_count_from_pytest_summary": int(match.group(1)) if match else None,
        "stdout": stdout,
        "stderr": stderr,
        "model_calls": 0,
        "gpu_calls": 0,
        "container_invocations": 0,
        "external_network_calls": 0,
        "network_scope": "loopback mock HTTP server only",
        "source_sha256": {name: sha256(HERE / name) for name in SOURCE_FILES},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in (
        "status", "returncode", "test_count_from_pytest_summary", "model_calls",
        "gpu_calls", "container_invocations", "external_network_calls",
    )}, sort_keys=True))
    return 0 if returncode == 0 and not timed_out else 1


if __name__ == "__main__":
    raise SystemExit(main())
