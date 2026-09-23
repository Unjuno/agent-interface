"""Fresh live negative control for typed independent-finish failure packaging."""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "results/timing-envelope-openttd-matched-03"
ROOT = BASE / "negative-control"
CONTROL = BASE / "negative-control-supervisor"
CONTROL.mkdir(parents=True, exist_ok=False)


def dump(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def linux(path):
    resolved = path.resolve()
    return "/mnt/" + resolved.drive[0].lower() + resolved.as_posix()[2:]


def wait_file(path, process, seconds=120):
    deadline = time.monotonic() + seconds
    while not path.exists():
        if process.poll() is not None:
            raise RuntimeError("driver exited before " + path.name)
        if time.monotonic() > deadline:
            raise TimeoutError(path.name)
        time.sleep(0.025)
    return read(path)


source_names = [
    "openttd_negative_finish_live_v1.py",
    "timing_envelope_openttd_matched_driver_v3.py",
    "timing_envelope_openttd_matched_supervisor_v3.py",
    "openttd_finish_outcome_v1.py",
]
dump(CONTROL / "plan.json", {
    "scope": "fresh no-input negative independent-finish packaging control",
    "sources": {
        name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        for name in source_names
    },
    "expected": "independent score false, typed visual_verify_false_positive, zero durable input calls",
})
started = time.perf_counter_ns()
driver = subprocess.Popen(
    ["wsl", "-d", "Ubuntu", "--", "python3", linux(HERE / "timing_envelope_openttd_matched_driver_v3.py"), "negative-control"],
    stdout=(CONTROL / "driver-stdout.txt").open("wb"),
    stderr=(CONTROL / "driver-stderr.txt").open("wb"),
)
try:
    ready = wait_file(ROOT / "ready.json", driver)
    dump(ROOT / "proposal-1.json", {
        "finish": True,
        "reason": "controlled finish request before any task input",
    })
    failure = wait_file(ROOT / "failure-evaluation.json", driver, 30)
    code = driver.wait(timeout=10)
    assert code == 0
    assert failure["success"] is False
    assert failure["failure_mode"] == "visual_verify_false_positive"
    assert failure["journal_calls"] == 0
    assert failure["evaluation"]["success"] is False
    assert not (ROOT / "result.json").exists()
    dump(CONTROL / "result.json", {
        "success": True,
        "driver_exit_code": code,
        "task": ready["task"],
        "failure_outcome": failure,
        "supervisor_wall_ms": (time.perf_counter_ns() - started) / 1e6,
        "scope": "fresh live packaging control; no model call and no task input",
    })
    print("openttd_negative_finish_live_v1: PASS")
finally:
    if driver.poll() is None:
        driver.terminate()
        driver.wait(timeout=10)
