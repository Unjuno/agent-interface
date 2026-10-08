"""One-shot outer process receipt for each preregistered ten-case batch."""
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
if len(sys.argv) != 2 or sys.argv[1] not in ("0", "1"):
    raise SystemExit("usage: supervise.py 0|1")
batch = int(sys.argv[1])
formal = root / "formal"
formal.mkdir(exist_ok=True)
out = formal / f"batch-{batch}"
if out.exists():
    raise SystemExit("consumed batch: refusal, no rerun")
if batch == 1:
    prior = json.loads((formal / "batch-0" / "EXIT.json").read_text())
    if prior["exit"] != 0 or prior["timed_out"]:
        raise SystemExit("prior batch did not complete")
cmd = [sys.executable, "-B", str(root / "study.py"), str(out), "--batch", str(batch)]
receipt = {"command": cmd, "start_ns": time.monotonic_ns(), "timed_out": False}
with (formal / f"batch-{batch}.stdout").open("xb") as stdout, (formal / f"batch-{batch}.stderr").open("xb") as stderr:
    proc = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, cwd=root, start_new_session=True)
    receipt["pid"] = proc.pid
    receipt["process_group"] = os.getpgid(proc.pid)
    try:
        receipt["exit"] = proc.wait(timeout=35)
    except subprocess.TimeoutExpired:
        receipt["timed_out"] = True
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            receipt["exit"] = proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            receipt["exit"] = proc.wait(timeout=2)
receipt["end_ns"] = time.monotonic_ns()
if not out.is_dir():
    # Preserve prelaunch failure outside the absent output, not a fabricated batch.
    target = formal / f"batch-{batch}.PRELAUNCH.json"
else:
    target = out / "EXIT.json"
with target.open("x") as f:
    json.dump(receipt, f, indent=2, sort_keys=True)
    f.write("\n")
print(json.dumps(receipt, sort_keys=True))
raise SystemExit(0 if receipt["exit"] == 0 and not receipt["timed_out"] else 1)
