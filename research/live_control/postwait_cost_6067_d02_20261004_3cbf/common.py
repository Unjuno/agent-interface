"""Exclusive receipts and monotonic deadlines (not a hard-real-time claim)."""
import json
import time
from pathlib import Path


def write(path, value):
    with Path(path).open("x") as f:
        json.dump(value, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")


def until(ns):
    # Excluded timer01 selected a 15ms final spin before any formal cell.
    # Same source/capture pacing, additional CPU cost, no hard-real-time claim.
    final_spin_ns = 15_000_000
    while True:
        remain = ns - time.monotonic_ns()
        if remain <= 0:
            return
        if remain > final_spin_ns:
            time.sleep((remain - final_spin_ns) / 1e9)


def await_file(path, seconds=4):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            return json.loads(Path(path).read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.002)
    raise RuntimeError("bounded readiness timeout")
