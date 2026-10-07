#!/usr/bin/env python3
"""Reproduce the pinned caller-progress candidate/control regression locally."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


MAIN = "abb6f6f9c71f7c61db77070f0ced3c4bc2439dcd"
CANDIDATE = "52d6b295c68e6c175d25aa9f52a58936c341983f"
SOURCE = "research/live_control/adaptive_acquisition_caller_v3.py"
TESTS = (
    "research/live_control/test_adaptive_acquisition_caller_terminal_v3.py",
    "research/live_control/test_adaptive_acquisition_caller_v3.py",
    "research/live_control/test_adaptive_acquisition_caller_verify_progress_v3.py",
)
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def gh_file(commit: str, path: str) -> bytes:
    response = subprocess.check_output(
        ["gh", "api", f"repos/Unjuno/agent-interface/contents/{path}?ref={commit}"]
    )
    return base64.b64decode(json.loads(response)["content"])


def run(command: list[str], cwd: Path, env: dict[str, str], label: str) -> int:
    result = subprocess.run(command, cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = result.stdout.replace(str(cwd), "<TEST_DIR>")
    (OUT / f"{label}.txt").write_text(text, encoding="utf-8")
    return result.returncode


def main() -> int:
    current_main = subprocess.check_output(
        ["git", "show", f"{MAIN}:{SOURCE}"], cwd=ROOT
    )
    candidate = gh_file(CANDIDATE, SOURCE)
    fetched_tests = {Path(path).name: gh_file(CANDIDATE, path) for path in TESTS}
    expected_main = "8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca"
    expected_candidate = "77cf5905c48ff4302d32007eeff5e75fcdbd5b2c5d88b00ec8d3def51b529130"
    if sha256(current_main) != expected_main:
        raise SystemExit("current-main source hash does not match the pinned main source")
    if sha256(candidate) != expected_candidate:
        raise SystemExit("candidate source hash does not match the pinned PR source")

    with tempfile.TemporaryDirectory(prefix="caller-progress-7234-") as temp_name:
        temp = Path(temp_name)
        candidate_dir = temp / "candidate"
        candidate_dir.mkdir()
        (candidate_dir / Path(SOURCE).name).write_bytes(candidate)
        for name, data in fetched_tests.items():
            (candidate_dir / name).write_bytes(data)
        candidate_modules = [Path(path).stem for path in TESTS]
        for label, optimization in (("candidate-normal", []), ("candidate-optimized", ["-O"])):
            env = os.environ.copy()
            rows = temp / f"{label}-rows.json"
            env.update(PYTHONPATH=f"{candidate_dir}:{ROOT / 'research/live_control'}:{ROOT}",
                       ROWS_OUTPUT=str(rows))
            code = run([sys.executable, *optimization, "-m", "unittest", "-v",
                        *candidate_modules], candidate_dir, env, label)
            if code != 0:
                raise SystemExit(f"{label} failed with exit code {code}")

        env = os.environ.copy()
        rows = temp / "candidate-progress-rows.json"
        env.update(PYTHONPATH=f"{candidate_dir}:{ROOT / 'research/live_control'}:{ROOT}",
                   ROWS_OUTPUT=str(rows))
        code = run([sys.executable, str(candidate_dir / "test_adaptive_acquisition_caller_verify_progress_v3.py")],
                   candidate_dir, env, "candidate-progress-rows")
        if code != 0:
            raise SystemExit("candidate progress row capture failed")
        (OUT / "CANDIDATE_ROWS.json").write_bytes(rows.read_bytes())

        control_dir = temp / "current-main"
        control_dir.mkdir()
        (control_dir / Path(SOURCE).name).write_bytes(current_main)
        progress_test = "test_adaptive_acquisition_caller_verify_progress_v3.py"
        (control_dir / progress_test).write_bytes(fetched_tests[progress_test])
        env = os.environ.copy()
        rows = temp / "current-main-rows.json"
        env.update(PYTHONPATH=f"{control_dir}:{ROOT / 'research/live_control'}:{ROOT}",
                   ROWS_OUTPUT=str(rows))
        code = run([sys.executable, str(control_dir / progress_test)], control_dir,
                   env, "CURRENT_MAIN_CONTROL")
        if code == 0:
            raise SystemExit("current-main regression control unexpectedly passed")
        (OUT / "CURRENT_MAIN_ROWS.json").write_bytes(rows.read_bytes())

    source_files = {
        "current_main_sha256": sha256(current_main),
        "candidate_sha256": sha256(candidate),
        "candidate_test_sha256": {name: sha256(data) for name, data in fetched_tests.items()},
    }
    (OUT / "SOURCE_HASHES.json").write_text(
        json.dumps({"main_commit": MAIN, "candidate_commit": CANDIDATE, **source_files},
                   indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote candidate normal/optimized logs, current-main control log, rows, and source hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
