import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text())

def check(condition, message):
    if not condition:
        raise SystemExit(message)

check(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
      == FREEZE["main_commit"], "STOP_MAIN_CHANGED")
for path, expected in FREEZE["source_sha256"].items():
    check(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected,
          "STOP_SOURCE_CHANGED:" + path)
for path, expected in FREEZE["artifact_sha256"].items():
    check(hashlib.sha256((HERE / path).read_bytes()).hexdigest() == expected,
          "STOP_ARTIFACT_CHANGED:" + path)
out = HERE / "results" / "A06"
out.mkdir(parents=True, exist_ok=True)
for name in ("RAW.jsonl", "candidate.stdout.txt", "candidate.stderr.txt", "candidate.exit.txt"):
    check(not (out / name).exists(), "STOP_OUTPUT_EXISTS:" + name)
proc = subprocess.run([sys.executable, str(HERE / "candidate.py")], cwd=ROOT,
                      text=True, capture_output=True)
(out / "candidate.stdout.txt").write_text(proc.stdout)
(out / "candidate.stderr.txt").write_text(proc.stderr)
(out / "candidate.exit.txt").write_text(str(proc.returncode) + "\n")
print(json.dumps({"candidate_exit": proc.returncode, "raw_exists": (out / "RAW.jsonl").exists()}))
raise SystemExit(proc.returncode)
