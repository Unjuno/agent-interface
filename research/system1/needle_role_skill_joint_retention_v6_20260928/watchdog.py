"""In-container hard-stop guard for the single leased formal invocation."""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def parse_deadline(value: str) -> datetime:
    deadline = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if deadline.tzinfo is None:
        raise ValueError("watchdog_deadline_must_be_zoned")
    return deadline.astimezone(timezone.utc)


def run_child(command: list[str], max_runtime_seconds: float, hard_stop_utc: str,
              receipt_path: Path, *, popen=subprocess.Popen,
              clock=time.monotonic, sleep=time.sleep) -> int:
    deadline = parse_deadline(hard_stop_utc)
    if not math.isfinite(max_runtime_seconds) or max_runtime_seconds <= 0:
        raise ValueError("watchdog_runtime_invalid")
    monotonic_deadline = clock() + max_runtime_seconds
    child = popen(command)
    timed_out = False
    while child.poll() is None:
        remaining = monotonic_deadline - clock()
        if remaining <= 0:
            timed_out = True
            child.terminate()
            try:
                child.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
            break
        sleep(min(0.25, remaining))
    exit_code = 124 if timed_out else child.returncode
    record = {
        "schema": "needle-formal-watchdog-receipt-v1",
        "hard_stop_utc": deadline.isoformat().replace("+00:00", "Z"),
        "max_runtime_seconds": max_runtime_seconds,
        "timed_out": timed_out,
        "child_exit_code": exit_code,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with receipt_path.open("xb") as stream:
        stream.write((json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode())
    return exit_code


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    deadline = os.environ.get("NEEDLE_HARD_STOP_UTC")
    max_runtime = os.environ.get("NEEDLE_HARD_STOP_SECONDS")
    if not deadline or not max_runtime or not args:
        raise SystemExit("watchdog requires hard-stop environment and a runner command")
    return run_child([sys.executable, "-B", *args], float(max_runtime), deadline,
                     Path("/out/watchdog_receipt.json"))


if __name__ == "__main__":
    raise SystemExit(main())
