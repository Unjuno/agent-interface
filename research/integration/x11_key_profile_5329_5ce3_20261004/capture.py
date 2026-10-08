"""Capture one named preparation/execution command without overwriting a record."""
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

destination = Path(sys.argv[1])
command = sys.argv[2:]
destination.parent.mkdir(parents=True, exist_ok=True)
with destination.open("x") as receipt:
    start = time.monotonic_ns()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900)
        record = {"returncode": process.returncode, "stdout": process.stdout.decode(errors="replace"), "stderr": process.stderr.decode(errors="replace")}
    except subprocess.TimeoutExpired as error:
        record = {"returncode": None, "stop": "COMMAND_TIMEOUT", "stdout": (error.stdout or b"").decode(errors="replace"), "stderr": (error.stderr or b"").decode(errors="replace")}
    record.update(command=command, started_utc=started, elapsed_ns=time.monotonic_ns()-start)
    json.dump(record, receipt, indent=2)
    receipt.write("\n")
print(json.dumps({"record": str(destination), "returncode": record["returncode"], "tail": record["stderr"][-1200:]}))
sys.exit(0 if record["returncode"] == 0 else 1)
