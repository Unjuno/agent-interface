"""Run the frozen synthetic composition once normally and once under -O."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


PACKET = Path(__file__).resolve().parent
REPO = PACKET.parents[3]
CONDITIONS = PACKET / "CONDITIONS.json"
TEST = PACKET / "test_provider_compiled_composition.py"
RAW = PACKET / "raw"
ATTEMPTS = PACKET / "attempts"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_bytes((json.dumps(value, indent=2) + "\n").encode("utf-8"))


def main():
    conditions = json.loads(CONDITIONS.read_text(encoding="utf-8"))
    if conditions.get("base_main_sha") != subprocess.check_output(
            ["git", "rev-parse", "origin/main"], cwd=REPO, text=True).strip():
        raise SystemExit("origin/main moved from the frozen base")
    if sys.version_info[:3] != (3, 13, 14):
        raise SystemExit(f"frozen interpreter mismatch: {sys.version}")
    for name, expected in conditions["source_sha256"].items():
        actual = sha256((REPO / name).read_bytes())
        if actual != expected:
            raise SystemExit(f"frozen source changed: {name}")
    if RAW.exists() or ATTEMPTS.exists():
        raise SystemExit("output roots already exist; refuse to overwrite evidence")
    RAW.mkdir()
    ATTEMPTS.mkdir()

    results = []
    for mode, optimization in (("normal", []), ("optimized", ["-O"])):
        mode_root = ATTEMPTS / mode
        mode_root.mkdir()
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO)
        env["ISSUE57_COMPOSITION_MODE"] = mode
        env["ISSUE57_COMPOSITION_EVIDENCE"] = str(ATTEMPTS)
        command = [sys.executable, "-B", *optimization, str(TEST), "-v"]
        started = time.perf_counter_ns()
        completed = subprocess.run(command, cwd=REPO, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        elapsed = time.perf_counter_ns() - started
        (RAW / f"{mode}.stdout.bin").write_bytes(completed.stdout)
        (RAW / f"{mode}.stderr.bin").write_bytes(completed.stderr)
        (RAW / f"{mode}.exitcode.txt").write_bytes(
            f"{completed.returncode}\n".encode("ascii"))
        results.append({
            "mode": mode,
            "command": command,
            "returncode": completed.returncode,
            "elapsed_ns": elapsed,
            "stdout_sha256": sha256(completed.stdout),
            "stderr_sha256": sha256(completed.stderr),
            "stdout_bytes": len(completed.stdout),
            "stderr_bytes": len(completed.stderr),
        })

    receipt = {
        "schema": "issue57-provider-compiled-run-result-r01",
        "frozen_base_main": conditions["base_main_sha"],
        "harness_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "python": sys.version,
        "executable": sys.executable,
        "runs": results,
    }
    write_json(PACKET / "run_results.json", receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if all(row["returncode"] == 0 for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
