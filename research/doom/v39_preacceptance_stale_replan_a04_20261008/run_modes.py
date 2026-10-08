"""Run A04 normally and optimized, preserving the exact raw outputs."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "run.py"


def run(label, options):
    proc = subprocess.run([sys.executable, *options, "-B", str(RUN)],
                          cwd=HERE.parents[2], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (HERE / f"{label}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (HERE / f"{label}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    (HERE / f"{label}.exit.txt").write_text(f"{proc.returncode}\n", encoding="ascii")
    if proc.returncode:
        raise SystemExit(f"{label} failed ({proc.returncode}); inspect retained stderr")
    return proc


normal = run("normal", [])
optimized = run("optimized", ["-O"])
if normal.stdout != optimized.stdout or normal.stderr != optimized.stderr:
    raise SystemExit("normal and optimized outputs differ")
result = json.loads(normal.stdout)
(HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print("PASS: normal and optimized outputs are byte-identical")
print(normal.stdout, end="")
