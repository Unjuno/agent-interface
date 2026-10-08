from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

OUT = Path(os.environ.get("OUT_DIR", "/out"))
TRIALS = Path(os.environ.get("TRIALS_JSON", "/src/formal-trials.json"))
OUT.mkdir(parents=True, exist_ok=True)
started = time.monotonic_ns()
with (OUT / "candidate.stdout.txt").open("wb") as stdout, (OUT / "candidate.stderr.txt").open("wb") as stderr:
    try:
        run = subprocess.run(["xvfb-run", "-a", "-e", "/out/xvfb.stderr.txt",
                              "-s", "-screen 0 800x600x24", "python3", "-B", "/src/fixture.py"],
                             env={**os.environ, "TRIALS_JSON": str(TRIALS)}, stdout=stdout,
                             stderr=stderr, timeout=180, check=False)
        code = run.returncode
    except subprocess.TimeoutExpired:
        code = 124
ended = time.monotonic_ns()
receipt = {"schema": "issue6526-a02-candidate-receipt-v1", "started_mono_ns": started,
           "ended_mono_ns": ended, "exit_code": code, "trial_file": TRIALS.name,
           "trial_count": len(json.loads(TRIALS.read_text()))}
(OUT / "candidate-receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2)+"\n")
print(json.dumps(receipt, sort_keys=True))
sys.exit(code)
