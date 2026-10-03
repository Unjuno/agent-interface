"""Exclusive receipts and monotonic deadlines (not a hard-real-time claim)."""
import json
import time
from pathlib import Path


def write(path, value):
    with Path(path).open("x") as f:
        json.dump(value, f, sort_keys=True, separators=(",", ":"))
        f.write("\n")


def until(ns):
    while True:
        remain = ns - time.monotonic_ns()
        if remain <= 0:
            return
        time.sleep(remain / 1e9)


def await_file(path, seconds=4):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            return json.loads(Path(path).read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.002)
    raise RuntimeError("bounded readiness timeout")
