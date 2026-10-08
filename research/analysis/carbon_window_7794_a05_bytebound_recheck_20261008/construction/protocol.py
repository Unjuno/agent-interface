"""Frozen case matrix and child-start synchronization primitives."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time


CASES = (
    {"name": "exit-0", "child_exit": 0},
    {"name": "exit-23", "child_exit": 23},
    {"name": "timeout-after-start", "child_exit": 0, "child_sleep": 8,
     "broker_timeout": 5},
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


def expected_case_names() -> tuple[str, ...]:
    return tuple(row["name"] for row in CASES)


def wait_until_started(marker: Path, call_log: Path, process,
                       timeout_s: float = 3.0) -> tuple[int, dict]:
    """Require a valid child call record and marker before timeout is evaluated."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if marker.is_file() and call_log.is_file():
            value = marker.read_text(encoding="utf-8")
            if value != "started\n":
                raise ValueError("unexpected child start marker")
            lines = call_log.read_text(encoding="utf-8").splitlines()
            if len(lines) != 1:
                raise ValueError("expected exactly one fsynced child call record")
            call = json.loads(lines[0])
            if not isinstance(call, dict) or call.get("event") != "child_started":
                raise ValueError("child call record does not prove start")
            return time.perf_counter_ns(), call
        if process.poll() is not None:
            raise RuntimeError("broker exited before child start marker")
        time.sleep(0.005)
    raise TimeoutError("child start marker not observed")
