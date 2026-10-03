"""One candidate, then one auditor, with durable subprocess receipts."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys


def main():
    out = pathlib.Path("/out")
    receipts = []
    for name, command in (
        ("candidate", [sys.executable, "-B", "/source/candidate.py", "/out/raw.jsonl"]),
        ("auditor", [sys.executable, "-B", "/source/audit.py", "/out/raw.jsonl", "/out/audit.json"]),
    ):
        start = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result = subprocess.run(command, capture_output=True, timeout=25)
        end = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (out / (name + ".stdout.txt")).write_bytes(result.stdout)
        (out / (name + ".stderr.txt")).write_bytes(result.stderr)
        receipts.append({"component": name, "command": command, "started_utc": start, "ended_utc": end,
                         "exit_code": result.returncode, "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                         "stderr_sha256": hashlib.sha256(result.stderr).hexdigest()})
        (out / "driver_receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
        if result.returncode:
            print(json.dumps({"status": "STOP", "receipts": receipts}))
            return result.returncode
    print(json.dumps({"status": "COMPLETE", "receipts": receipts}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
