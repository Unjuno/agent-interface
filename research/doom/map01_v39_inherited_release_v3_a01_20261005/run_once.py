"""Capture one frozen probe invocation without changing its raw stdout."""
import subprocess
import sys
from pathlib import Path

pkg = Path(__file__).resolve().parent
run = subprocess.run([sys.executable, str(pkg / "probe.py")],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
(pkg / "results" / "stdout.txt").write_text(run.stdout)
(pkg / "results" / "stderr.txt").write_text(run.stderr)
(pkg / "results" / "exit_code.txt").write_text(f"{run.returncode}\n")
sys.stdout.write(run.stdout)
sys.stderr.write(run.stderr)
raise SystemExit(run.returncode)
