import hashlib
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
stage = sys.argv[1]
if stage == "candidate":
    command = [sys.executable, str(ROOT / "candidate.py"), str(ROOT / "out/observations.json"), str(ROOT / "out/candidate.json")]
elif stage == "auditor":
    command = [sys.executable, str(ROOT / "auditor.py"), str(ROOT), str(ROOT / "out/audit.json")]
else:
    raise SystemExit("invalid stage")
started = time.time_ns()
p = subprocess.run(command, capture_output=True)
ended = time.time_ns()
stage_dir = ROOT / "out" / "process" / stage
stage_dir.mkdir(exist_ok=False)
(stage_dir / "stdout.bin").write_bytes(p.stdout)
(stage_dir / "stderr.bin").write_bytes(p.stderr)
record = {"stage": stage, "command": command, "exit": p.returncode, "started_unix_ns": started, "ended_unix_ns": ended,
          "stdout_sha256": hashlib.sha256(p.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(p.stderr).hexdigest(),
          "stdout_bytes": len(p.stdout), "stderr_bytes": len(p.stderr)}
(stage_dir / "receipt.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, sort_keys=True))
raise SystemExit(p.returncode)
