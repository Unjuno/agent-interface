import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = Path(os.environ.get("SOURCE_ROOT", ROOT))
MODE = sys.argv[1] if len(sys.argv) == 2 else ""
if MODE not in ("baseline", "candidate"):
    raise SystemExit("Usage: python run_unit_suite.py baseline|candidate")

if MODE == "baseline":
    test_root = SOURCE_ROOT / "research" / "doom"
    pythonpath = os.pathsep.join((
        str(test_root), str(SOURCE_ROOT / "research" / "live_control")
    ))
    output = ROOT / "results" / "a01" / "UNIT_BASELINE.txt"
else:
    test_root = ROOT / "candidate" / "research" / "doom"
    pythonpath = os.pathsep.join((
        str(test_root), str(SOURCE_ROOT / "research" / "live_control")
    ))
    output = ROOT / "results" / "a01" / "UNIT_CANDIDATE.txt"
if output.exists():
    raise SystemExit("STOP_UNIT_OUTPUT_EXISTS")

command = [
    sys.executable, "-m", "unittest",
    "test_doom_typed_artifact_reconciliation_v1", "-v",
]
env = dict(os.environ)
env["PYTHONPATH"] = pythonpath
run = subprocess.run(command, cwd=ROOT, env=env, text=True,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
payload = (
    f"mode={MODE}\n"
    f"command={json.dumps(command)}\n"
    f"exit={run.returncode}\n"
    f"--- stdout ---\n{run.stdout}"
    f"--- stderr ---\n{run.stderr}"
)
output.write_text(payload, encoding="utf-8")
print(json.dumps({
    "mode": MODE, "exit": run.returncode,
    "output": str(output.relative_to(ROOT)),
    "summary": next((line.strip() for line in
                     (run.stdout + run.stderr).splitlines()
                     if line.strip().startswith("Ran ")), None),
}, sort_keys=True))
