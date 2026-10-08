"""Execute current-main integration replay under cached, offline WSLc."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
OUT = PACKAGE / "results" / "current-main-a01"
IMAGE = "agent-interface/native-suite-wslc-a08:20261004"
TESTS = {
    "focused": [
        "research.live_control.test_observable_signal_guard_v2",
        "research.doom.test_map01_overlap_controller_v39",
    ],
    "adjacent": [
        "research.doom.test_overlap_controller_v39_wait",
        "research.doom.test_controller_failure_cleanup_v1",
        "research.doom.test_map01_overlap_controller_v39_dual_signal",
        "research.doom.test_map01_overlap_controller_v39_pair_duplicate_consistency",
        "research.doom.test_map01_v39_pair_wait_dispatch",
    ],
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    mount_source = str(ROOT).replace("\\", "/")
    hashes = json.loads((PACKAGE / "FREEZE.json").read_text())["implementation_files"]
    actual_hashes = {name: sha256(ROOT / name) for name in hashes}
    if actual_hashes != hashes:
        raise SystemExit(f"source changed after freeze: {actual_hashes!r}")
    receipts = {}

    for label, modules in TESTS.items():
        command = [
            "wslc.exe", "run", "--rm", "--pull", "never", "--network", "none",
            "--cpus", "1", "--name", f"inv59-current-main-a01-{label}",
            "--mount", f"type=bind,source={mount_source},target=/src,readonly",
            "--workdir", "/src",
            "--env", "PYTHONPATH=/src/research/doom:/src/research/live_control:/src",
            "--entrypoint", "python", IMAGE, "-B", "-m", "unittest", "-v",
            *modules,
        ]
        started = time.time_ns()
        completed = subprocess.run(command, cwd=ROOT, capture_output=True)
        finished = time.time_ns()
        (OUT / f"{label}.stdout.log").write_bytes(completed.stdout)
        (OUT / f"{label}.stderr.log").write_bytes(completed.stderr)
        raw_argv_sha256 = hashlib.sha256(
            json.dumps(command, separators=(",", ":"), ensure_ascii=True).encode()
        ).hexdigest()
        redacted_mount = f"source={mount_source},target=/src,readonly"
        public_command = [
            argument.replace(redacted_mount, "source=<repo>,target=/src,readonly")
            for argument in command
        ]
        receipts[label] = {
            "argv": public_command,
            "executed_argv_sha256": raw_argv_sha256,
            "mount_path_redacted": True,
            "started_unix_ns": started,
            "finished_unix_ns": finished,
            "returncode": completed.returncode,
            "source_sha256": hashes,
            "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        }
        print(f"{label}: exit={completed.returncode}")
        print(completed.stdout.decode("utf-8", errors="replace"))
        print(completed.stderr.decode("utf-8", errors="replace"))

    (OUT / "runs.json").write_text(json.dumps(receipts, indent=2) + "\n",
                                   encoding="utf-8")
    return 0 if all(row["returncode"] == 0 for row in receipts.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
