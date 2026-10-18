from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

OUT = Path("/out")


def invoke(label, script, *arguments):
    command = [sys.executable, "-B", script, *arguments]
    result = subprocess.run(command, cwd="/src", capture_output=True, text=True, check=False)
    (OUT / f"{label}.stdout.txt").write_text(result.stdout)
    (OUT / f"{label}.stderr.txt").write_text(result.stderr)
    return {"command": command, "exit_code": result.returncode}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    candidate = invoke("candidate", "candidate.py", "/out/candidate-output.json")
    audit = {"command": None, "exit_code": None}
    if candidate["exit_code"] == 0:
        audit = invoke(
            "auditor", "audit.py", "/out/candidate-output.json", "/out/audit-output.json",
            "/src/FREEZE_A02.json",
        )
    run = {
        "schema": "preference-manipulation-7678-t0-a02-run-v1",
        "allocation": "PREFERENCE-MANIPULATION-7678-T0-A02-20261005-01",
        "candidate_invocations": 1,
        "auditor_invocations": int(candidate["exit_code"] == 0),
        "retry_count": 0,
        "candidate": candidate,
        "auditor": audit,
    }
    (OUT / "RUN.json").write_text(json.dumps(run, indent=2, sort_keys=True) + "\n")
    print(json.dumps(run, sort_keys=True))
    return 0 if candidate["exit_code"] == 0 and audit["exit_code"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
