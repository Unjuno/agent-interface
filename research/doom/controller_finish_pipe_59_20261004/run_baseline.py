"""Run the frozen baseline probe once inside the cached CPU-only WSLc image."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "baseline-run-02"
IMAGE = "sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    checks = {
        "cleanup_source": digest(ROOT / "source/doom_controller_failure_cleanup_v1.py"),
        "probe": digest(ROOT / "probe_finish_pipe_01.py"),
    }
    expected = {key: freeze["sha256"][key] for key in checks}
    if checks != expected:
        raise SystemExit(f"freeze mismatch: actual={checks!r} expected={expected!r}")
    OUT.mkdir(exist_ok=True)
    source = (ROOT / "source").resolve().as_posix()
    output = OUT.resolve().as_posix()
    command = [
        "C:/Program Files/WSL/wslc.exe", "run", "--rm", "--pull", "never",
        "--name", "ai59-4d74-finish-pipe-baseline01",
        "--network", "none", "--user", "65534:65534", "--cpus", "1",
        "--memory", "512m", "--workdir", "/study", "--tmpfs", "/tmp",
        "--mount", f"type=bind,source={source},target=/study/source,readonly",
        "--mount", f"type=bind,source={(ROOT / 'probe_finish_pipe_01.py').resolve().as_posix()},target=/study/probe_finish_pipe_01.py,readonly",
        "--mount", f"type=bind,source={output},target=/out",
        "--env", "PYTHONDONTWRITEBYTECODE=1", IMAGE,
        "timeout", "30s", "python3", "-B", "/study/probe_finish_pipe_01.py",
        "--source", "/study/source", "--out", "/out",
    ]
    (OUT / "argv.json").write_text(json.dumps(command, indent=2) + "\n",
                                    encoding="utf-8")
    completed = subprocess.run(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, check=False)
    (OUT / "stdout.bin").write_bytes(completed.stdout)
    (OUT / "stderr.bin").write_bytes(completed.stderr)
    (OUT / "exit-code.txt").write_text(str(completed.returncode) + "\n",
                                        encoding="ascii")
    print(f"exit_code={completed.returncode}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
