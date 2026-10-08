import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
run = subprocess.run(
    [sys.executable, "-B", str(root / "audit.py")],
    capture_output=True,
    text=True,
)
(root / "AUDIT.stdout.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
(root / "AUDIT.exit.txt").write_text(f"{run.returncode}\n", encoding="ascii")
if run.returncode:
    raise SystemExit(run.returncode)
subprocess.run([sys.executable, "-B", str(root / "hash_package.py")], check=True)
print("audit and package checksums PASS")

