"""Run one frozen text-mode follow-up probe; propagate every unexpected code."""
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
OUT = ROOT / "run-01"
IMAGE = "sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    paths = {
        "preregistration": ROOT / "PREREGISTRATION.md",
        "probe": ROOT / "probe.py",
        "runner": Path(__file__),
        "auditor": ROOT / "audit.py",
        "source": PACKAGE / "source/doom_controller_failure_cleanup_v1.py",
    }
    actual = {name: digest(path) for name, path in paths.items()}
    expected = {name: freeze["sha256"][name] for name in paths}
    if actual != expected:
        raise SystemExit(f"freeze mismatch: actual={actual!r}")
    OUT.mkdir(exist_ok=False)
    command = [
        "C:/Program Files/WSL/wslc.exe", "run", "--rm", "--pull", "never",
        "--name", "ai59-finish-pipe-followup-01", "--network", "none",
        "--user", "65534:65534", "--cpus", "1", "--memory", "512m",
        "--workdir", "/study", "--tmpfs", "/tmp",
        "--mount", f"type=bind,source={(PACKAGE / 'source').resolve().as_posix()},target=/study/source,readonly",
        "--mount", f"type=bind,source={ROOT / 'probe.py'},target=/study/probe.py,readonly",
        "--mount", f"type=bind,source={OUT.resolve().as_posix()},target=/out",
        "--env", "PYTHONDONTWRITEBYTECODE=1", IMAGE,
        "timeout", "30s", "python3", "-B", "/study/probe.py",
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
    return completed.returncode if completed.returncode else 0


if __name__ == "__main__":
    raise SystemExit(main())
