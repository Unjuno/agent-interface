"""Hash-gated one-shot candidate launcher; writes evidence without overwriting."""

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent
RESULTS = ROOT / "results"
FROZEN_FILES = [
    "FREEZE.md", "candidate.py", "fixture.json", "EXPECTED.json", "audit.py", "test_method.py",
    "execute_once.py", "audit_once.py",
]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    with path.open("xb") as stream:
        stream.write(data)


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    for name in FROZEN_FILES:
        actual = sha256((ROOT / name).read_bytes())
        if actual != freeze["frozen_source_sha256"][name]:
            raise SystemExit(f"STOP_FROZEN_SOURCE_MISMATCH:{name}:{actual}")
    if RESULTS.exists():
        raise SystemExit("STOP_OUTPUT_PATH_NOT_EMPTY")
    RESULTS.mkdir()

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    child = subprocess.run(
        [sys.executable, str(ROOT / "candidate.py")],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    write_new(RESULTS / "candidate.stdout.json", child.stdout)
    write_new(RESULTS / "candidate.stderr.txt", child.stderr)
    source_hashes = {name: sha256((ROOT / name).read_bytes()) for name in FROZEN_FILES}
    run = {
        "schema": "issue-5841-candidate-run-v1",
        "allocation": freeze["allocation"],
        "base_main": freeze["base_main"],
        "candidate_invocations": 1,
        "candidate_exit_code": child.returncode,
        "stdout_sha256": sha256(child.stdout),
        "stderr_sha256": sha256(child.stderr),
        "source_sha256": source_hashes,
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "container": False,
        "docker_preflight": "STOP_ENGINE_PROBE_TIMEOUT_4S",
    }
    write_new(RESULTS / "RUN.json", (json.dumps(run, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps({"exit_code": child.returncode, "stdout_sha256": run["stdout_sha256"]}, sort_keys=True))
    return child.returncode


if __name__ == "__main__":
    raise SystemExit(main())
