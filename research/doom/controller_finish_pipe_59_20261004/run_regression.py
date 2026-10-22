"""Run the one real-child finish-pipe regression in isolated WSLc."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
IMAGE = "sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("red", "green"))
    phase = parser.parse_args().phase
    freeze = json.loads((ROOT / "REPAIR_FREEZE.json").read_text(encoding="utf-8"))
    candidate = ROOT / "candidate/doom_controller_failure_cleanup_v1.py"
    test = ROOT / "test_cleanup_finish_pipe.py"
    runner_hash = digest(Path(__file__))
    if runner_hash != freeze["runner_sha256"] or digest(test) != freeze["test_sha256"]:
        raise SystemExit("repair runner or regression test differs from freeze")
    if digest(candidate) != freeze[f"{phase}_candidate_sha256"]:
        raise SystemExit(f"{phase} candidate source differs from freeze")
    out = ROOT / f"repair-{phase}-run"
    out.mkdir(exist_ok=True)
    command = [
        "C:/Program Files/WSL/wslc.exe", "run", "--rm", "--pull", "never",
        "--name", f"ai59-4d74-finish-pipe-{phase}", "--network", "none",
        "--user", "65534:65534", "--cpus", "1", "--memory", "512m",
        "--workdir", "/tests", "--tmpfs", "/tmp",
        "--mount", f"type=bind,source={candidate.parent.resolve().as_posix()},target=/candidate,readonly",
        "--mount", f"type=bind,source={test.resolve().as_posix()},target=/tests/test_cleanup_finish_pipe.py,readonly",
        "--mount", f"type=bind,source={out.resolve().as_posix()},target=/out",
        "--env", "PYTHONPATH=/candidate", "--env", "PYTHONDONTWRITEBYTECODE=1",
        IMAGE, "timeout", "20s", "python3", "-B", "-m", "unittest", "-v",
        "test_cleanup_finish_pipe",
    ]
    (out / "argv.json").write_text(json.dumps(command, indent=2) + "\n",
                                    encoding="utf-8")
    completed = subprocess.run(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, check=False)
    (out / "stdout.bin").write_bytes(completed.stdout)
    (out / "stderr.bin").write_bytes(completed.stderr)
    (out / "exit-code.txt").write_text(str(completed.returncode) + "\n",
                                        encoding="ascii")
    print(f"phase={phase} exit_code={completed.returncode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
