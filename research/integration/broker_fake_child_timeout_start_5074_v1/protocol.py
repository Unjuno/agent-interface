"""Frozen case matrix and child-start synchronization primitives."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time


CASES = (
    {"name": "exit-0", "child_exit": 0},
    {"name": "exit-23", "child_exit": 23},
    {"name": "timeout-after-start", "child_exit": 0, "child_sleep": 5,
     "broker_timeout": 2},
    {"name": "missing-executable", "missing": True},
    {"name": "malformed-json", "malformed": True},
    {"name": "idle-once", "idle": True},
    {"name": "sorted-once", "queued": True},
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
                    encoding="utf-8")


def wait_for_marker(marker: Path, process, timeout_s: float = 3.0) -> int:
    """Return monotonic timestamp after marker is readable; otherwise raise."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if marker.is_file():
            data = marker.read_text(encoding="utf-8")
            if data != "started\n":
                raise ValueError("child start marker content mismatch")
            return time.monotonic_ns()
        if process.poll() is not None:
            break
        time.sleep(0.005)
    raise TimeoutError("child-start marker absent before timeout gate")


def expected_case_names() -> tuple[str, ...]:
    return tuple(row["name"] for row in CASES)


def wait_until_started(marker: Path, process, timeout_s: float = 3.0) -> int:
    """Wait for a newline-terminated marker before arming the broker timeout."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if marker.is_file():
            value = marker.read_text(encoding="utf-8")
            if value != "started\n":
                raise ValueError("unexpected child start marker")
            return time.monotonic_ns()
        if process.poll() is not None:
            raise RuntimeError("broker exited before child start marker")
        time.sleep(0.005)
    raise TimeoutError("child start marker not observed")
