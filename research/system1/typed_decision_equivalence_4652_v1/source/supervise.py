#!/usr/bin/env python3
"""One-shot local formal supervisor; timeout is terminal, never retried."""

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout-seconds", type=int, default=1800)
    args = ap.parse_args()
    out = Path(args.out).resolve()
    if out.exists():
        raise SystemExit("OUTPUT_EXISTS_NO_RETRY")
    out.parent.mkdir(parents=True, exist_ok=True)
    runner = Path(args.study) / "source" / "formal_runner.py"
    command = [sys.executable, "-B", str(runner), "--study", args.study,
               "--model", args.model, "--corpus", args.corpus, "--out", str(out)]
    stdout_path = out.parent / (out.name + ".stdout")
    stderr_path = out.parent / (out.name + ".stderr")
    started_ns = time.time_ns()
    timed_out = False
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(command, cwd=runner.parent, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        try:
            return_code = process.wait(timeout=args.timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=5)
            except Exception:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except Exception:
                    pass
                process.wait()
            return_code = 124

    rows_path = out / "ROWS.jsonl"
    row_count = sum(1 for line in rows_path.open("rb") if line.strip()) if rows_path.exists() else 0
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "typed-decision-equivalence-supervisor-v1",
        "status": "STOP_SUPERVISOR_TIMEOUT" if timed_out else ("FORMAL_COMPLETE" if return_code == 0 else "STOP_RUNNER_NONZERO"),
        "return_code": return_code, "timeout_seconds": args.timeout_seconds,
        "started_ns": started_ns, "ended_ns": time.time_ns(), "formal_invocation_count": 1,
        "retained_rows": row_count,
        "rows_sha256": sha(rows_path) if rows_path.exists() else None,
        "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
        "command": command,
    }
    write_json(out.parent / (out.name + ".SUPERVISOR.json"), result)
    if timed_out or return_code != 0:
        write_json(out / "STOP.json", {
            "schema": "typed-decision-equivalence-stop-v1", "reason": result["status"],
            "formal_invocation_count": 1, "retained_rows": row_count,
            "rows_sha256": result["rows_sha256"], "stdout_sha256": result["stdout_sha256"],
            "stderr_sha256": result["stderr_sha256"],
        })
    print(json.dumps(result, sort_keys=True))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
