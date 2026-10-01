from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import transform

HERE = Path(__file__).resolve().parent
OUT = HERE / "run"
RAW = HERE / "candidate.raw.json"


def wsl_path(path: Path) -> str:
    return subprocess.check_output(["wsl.exe", "wslpath", "-a", str(path)], text=True).strip()


def main() -> int:
    if OUT.exists() or RAW.exists():
        raise SystemExit("STOP_T3_ONE_SHOT_OUTPUT_EXISTS")
    frozen = json.loads((HERE / "FREEZE_T3.json").read_text())
    for name, expected in frozen["analysis_sources_sha256"].items():
        actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"STOP_T3_FROZEN_SOURCE_CHANGED:{name}")
    reconstruction = transform.reconstruct_sources()
    derived = transform.derive()
    for name, record in derived.items():
        actual = hashlib.sha256((transform.DERIVED / name).read_bytes()).hexdigest()
        if actual != record["derived_sha256"]:
            raise SystemExit(f"STOP_DERIVED_SOURCE_HASH:{name}")
    run_path, runner_path = wsl_path(OUT), wsl_path(HERE / "runner.py")
    app_path, observer_path = wsl_path(transform.DERIVED / "app.py"), wsl_path(transform.DERIVED / "observer.py")
    cmd = f"xvfb-run -a -s '-screen 0 1024x768x24' python3 '{runner_path}' '{run_path}' '{app_path}' '{observer_path}'"
    proc = subprocess.run(["wsl.exe", "-e", "bash", "-lc", cmd], capture_output=True, text=True, timeout=30)
    trace = OUT / "run.raw.json"
    run = json.loads(trace.read_text()) if trace.exists() else None
    result = {"schema": "blackstart-source-bound-t3-candidate-v1", "source_reconstruction": reconstruction,
              "derived_sources": derived, "runner_exit_code": proc.returncode,
              "runner_stdout": proc.stdout[-2000:], "runner_stderr": proc.stderr[-2000:], "run": run}
    RAW.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
