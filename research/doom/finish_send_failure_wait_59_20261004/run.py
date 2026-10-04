"""Run a frozen child-pipe finish-failure regression in WSLc."""
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
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    source = ROOT / ("baseline" if phase == "red" else "candidate") / "doom_controller_failure_cleanup_v1.py"
    test = ROOT / "test_finish_send_failure_wait.py"
    if digest(Path(__file__)) != freeze["runner_sha256"]:
        raise SystemExit("runner differs from freeze")
    if digest(test) != freeze["test_sha256"]:
        raise SystemExit("test differs from freeze")
    if digest(source) != freeze[f"{phase}_source_sha256"]:
        raise SystemExit("source differs from freeze")
    out = ROOT / f"{phase}-run"
    out.mkdir(exist_ok=True)
    command = [
        "C:/Program Files/WSL/wslc.exe", "run", "--rm", "--pull", "never",
        "--name", f"ai59-finish-send-failure-{phase}", "--network", "none",
        "--user", "65534:65534", "--cpus", "1", "--memory", "512m",
        "--workdir", "/tests", "--tmpfs", "/tmp",
        "--mount", f"type=bind,source={source.parent.resolve().as_posix()},target=/candidate,readonly",
        "--mount", f"type=bind,source={test.resolve().as_posix()},target=/tests/test_finish_send_failure_wait.py,readonly",
        "--mount", f"type=bind,source={out.resolve().as_posix()},target=/out",
        "--env", "PYTHONPATH=/candidate", "--env", "PYTHONDONTWRITEBYTECODE=1",
        IMAGE, "timeout", "20s", "python3", "-B", "-m", "unittest", "-v",
        "test_finish_send_failure_wait",
    ]
    (out / "argv.json").write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (out / "stdout.bin").write_bytes(result.stdout)
    (out / "stderr.bin").write_bytes(result.stderr)
    (out / "exit-code.txt").write_text(str(result.returncode) + "\n", encoding="ascii")
    print(f"phase={phase} exit_code={result.returncode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
