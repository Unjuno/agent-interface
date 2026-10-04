"""Run the pinned alias regression against one explicit owner source copy."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
source = ROOT / sys.argv[1] / "input_owner_v12.py"
env = os.environ.copy()
env["INPUT_OWNER_V12_SOURCE"] = str(source)
run = subprocess.run(
    [sys.executable, "-B", "-m", "unittest",
     "research.live_control.test_input_owner_v12_unmatched_keyup_alias", "-v"],
    cwd=REPO, env=env, text=True, stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT, check=False)
(ROOT / f"{sys.argv[1]}.stdout.txt").write_text(run.stdout)
(ROOT / f"{sys.argv[1]}.exit.txt").write_text(f"{run.returncode}\n")
print(run.stdout, end="")
raise SystemExit(run.returncode)
