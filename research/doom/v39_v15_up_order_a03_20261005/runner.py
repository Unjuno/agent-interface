import json
import hashlib
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
freeze = json.loads((root / "FREEZE.json").read_text())
bad = []
for relpath, expected in freeze["sha256"].items():
    observed = hashlib.sha256((root / relpath).read_bytes()).hexdigest()
    if observed != expected:
        bad.append({"path": relpath, "expected": expected, "observed": observed})
if bad:
    print(json.dumps({"status": "STOP_FREEZE_HASH_MISMATCH", "candidate_started": False, "mismatches": bad}, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0)
candidate = subprocess.run(
    [sys.executable, str(root / "candidate.py")],
    capture_output=True,
    text=True,
)
if candidate.returncode != 0:
    print(json.dumps({
        "status": "STOP_CANDIDATE_PROCESS",
        "candidate_started": True,
        "candidate_exit": candidate.returncode,
        "stdout": candidate.stdout,
        "stderr": candidate.stderr,
        "auditor_started": False,
    }, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0)
try:
    raw = json.loads(candidate.stdout)
except Exception as exc:
    print(json.dumps({
        "status": "STOP_RAW_PARSE",
        "candidate_started": True,
        "candidate_exit": 0,
        "parse_error": repr(exc),
        "stdout": candidate.stdout,
        "stderr": candidate.stderr,
        "auditor_started": False,
    }, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0)
audit = subprocess.run(
    [sys.executable, str(root / "audit.py")],
    input=candidate.stdout,
    capture_output=True,
    text=True,
)
try:
    audit_result = json.loads(audit.stdout)
except Exception as exc:
    audit_result = {"parse_error": repr(exc), "stdout": audit.stdout}
print(json.dumps({
    "status": "AUDIT_COMPLETED" if audit.returncode == 0 else "AUDIT_PROCESS_ERROR",
    "candidate_started": True,
    "candidate_exit": candidate.returncode,
    "candidate_stderr": candidate.stderr,
    "raw": raw,
    "auditor_started": True,
    "audit_exit": audit.returncode,
    "audit": audit_result,
    "audit_stderr": audit.stderr,
}, sort_keys=True, separators=(",", ":")))
