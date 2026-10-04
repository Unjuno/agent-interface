"""Capture one expected-red baseline and the A05 focused/full green suites."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def run(argv, env=None):
    result = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "argv": argv,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


red_env = os.environ.copy()
red_env["PYTHONPATH"] = str(ROOT)
red = run([sys.executable, "initial-red/test_unknown_kind_probe.py"], env=red_env)
green_a05 = run([sys.executable, "-m", "unittest", "discover", "-s", ".", "-v"])
green_a04 = run([
    sys.executable, "-m", "unittest", "discover", "-s",
    str(ROOT.parent / "scorer_feedback_attribution_59_t0_a04_20261004"), "-v",
])
compile_check = run([
    sys.executable, "-m", "py_compile", "scorer_feedback_attribution_v4.py",
    "test_unknown_kind.py", "scorer_feedback_attribution_v3.py",
])

result = {
    "schema": "scorer-feedback-attribution-a05-result-v1",
    "python": sys.version,
    "base_commit": "8ddf0925539d03733d803b469586fb74a5b444e0",
    "current_main_commit": "af6d0f9842a2377fba736d2d65643b02690f99d9",
    "producer_contract": {
        "path": "research/doom/independent_progress_clock_v2.py",
        "sha256": "3d906a7043f0d674bac3bd137952adeac11c77c9339bc38ef6ca37b05e0d1613",
        "positive_useful_kinds": ["KILL_COUNT_INCREASE", "MAP_EXIT"],
        "other_source_kinds": ["DEATH_COUNT_INCREASE", "PLAYER_DEAD", "EPISODE_FINISHED_NO_EXIT"],
    },
    "source_sha256": {
        name: digest(name) for name in (
            "scorer_feedback_attribution_v3.py",
            "scorer_feedback_attribution_v4.py",
            "initial-red/test_unknown_kind_probe.py",
            "test_unknown_kind.py",
            "FREEZE.json",
            "README.md",
            "run.py",
        )
    },
    "red_baseline": red,
    "green_a05_suite": green_a05,
    "green_a04_suite": green_a04,
    "py_compile": compile_check,
    "docker": {
        "status": "STOP_NOT_RUN",
        "commands": ["docker image ls --digests", "docker pull python:3.12-slim"],
        "image_list_exit": 1,
        "image_list_stderr": "containerd blob sha256:c8fec4d7541b306b9266ce8d7800abad8e665e63d6ea1e5f62574d4b122a28d1 open failed: operation not supported",
        "pull_exit": 1,
        "pull_stderr": "containerd blob sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f lease/open failed: operation not supported",
    },
    "disposition": (
        "PASS_HOST_CONSTRUCTION_STOP_CONTAINER" if
        red["exit_code"] == 1 and "SINGLE_POSSIBLE_INTENT_ENVELOPE" in red["stderr"]
        and green_a05["exit_code"] == 0 and green_a04["exit_code"] == 0
        and compile_check["exit_code"] == 0
        else "FAIL_A05_CHECKS"
    ),
}
(ROOT / "A05_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "disposition": result["disposition"],
    "red_exit": red["exit_code"],
    "a05_suite_exit": green_a05["exit_code"],
    "a05_suite_summary": green_a05["stderr"].splitlines()[-3:],
    "a04_suite_exit": green_a04["exit_code"],
    "a04_suite_summary": green_a04["stderr"].splitlines()[-3:],
    "py_compile_exit": compile_check["exit_code"],
    "docker": result["docker"],
}, sort_keys=True))
raise SystemExit(0 if result["disposition"] == "PASS_HOST_CONSTRUCTION_STOP_CONTAINER" else 1)
