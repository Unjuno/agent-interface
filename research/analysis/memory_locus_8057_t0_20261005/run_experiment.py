"""Run candidate then independent auditor as separate Python processes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


out = Path("/out")
out.mkdir(exist_ok=True)
candidate = subprocess.run([sys.executable, "candidate.py"], check=False,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(out / "candidate.stdout.json").write_bytes(candidate.stdout)
(out / "candidate.stderr.txt").write_bytes(candidate.stderr)
audit = subprocess.run([sys.executable, "audit.py", "/out/candidate.stdout.json"],
                       check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(out / "audit.stdout.json").write_bytes(audit.stdout)
(out / "audit.stderr.txt").write_bytes(audit.stderr)
raw = json.loads(candidate.stdout)
summary = {}
for arm in ("NEITHER", "PRIVATE_NOTE", "ENVIRONMENT_CUE", "BOTH"):
    rows = [row for row in raw if row["arm"] == arm]
    summary[arm] = {
        "rows": len(rows),
        "task_correct": sum(row["task_correct"] for row in rows),
        "safety_pass": sum(row["safety_pass"] for row in rows),
        "total_cost_units": sum(row["total_cost"] for row in rows),
    }
run_record = {
    "candidate_exit": candidate.returncode,
    "candidate_stdout_sha256": hashlib.sha256(candidate.stdout).hexdigest(),
    "candidate_rows": len(raw),
    "audit_exit": audit.returncode,
    "audit_stdout_sha256": hashlib.sha256(audit.stdout).hexdigest(),
    "audit_stdout": audit.stdout.decode("utf-8").strip(),
    "summary": summary,
}
(out / "RUN.json").write_text(json.dumps(run_record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(run_record, sort_keys=True, separators=(",", ":")))
raise SystemExit(0 if candidate.returncode == 0 and audit.returncode == 0 else 1)
