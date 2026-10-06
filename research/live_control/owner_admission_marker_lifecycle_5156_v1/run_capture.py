"""Run and retain the marker probe's stdout, stderr, and exit code."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
probe = subprocess.run(
    [sys.executable, "-B", str(HERE / "run_probe.py")],
    cwd=HERE.parents[2], capture_output=True, text=True,
)
(HERE / "results/RAW_PROBE.txt").write_text(
    probe.stdout + probe.stderr, encoding="utf-8")
(HERE / "results/EXIT_CODE.txt").write_text(
    f"{probe.returncode}\n", encoding="utf-8")
print(probe.stdout, end="")
print(probe.stderr, end="", file=sys.stderr)
raise SystemExit(probe.returncode)
