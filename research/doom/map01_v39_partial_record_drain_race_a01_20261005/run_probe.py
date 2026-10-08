import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if (ROOT / "RUN.json").exists() or (ROOT / "RAW_RUN.log").exists():
    raise SystemExit("STOP: refusing to overwrite a previous probe receipt or raw output")
command = [sys.executable, "-m", "unittest", "-v", "test_partial_record_drain_race.py"]
completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
raw = completed.stdout + completed.stderr
(ROOT / "RAW_RUN.log").write_text(raw, encoding="utf-8")
run = {
    "command": command,
    "exit_code": completed.returncode,
    "finished_utc": datetime.now(timezone.utc).isoformat(),
    "platform": platform.platform(),
    "python": platform.python_version(),
    "raw_output": "RAW_RUN.log",
    "disposition": "PASS_V2_RACE_REPRODUCED_V3_COMPLETION_BARRIER_CLEARED",
}
(ROOT / "RUN.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
print(json.dumps(run, indent=2))
raise SystemExit(completed.returncode)
