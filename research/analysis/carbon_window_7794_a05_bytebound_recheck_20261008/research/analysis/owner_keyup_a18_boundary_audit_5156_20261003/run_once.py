import datetime
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    out = Path(sys.argv[1])
    out.mkdir(exist_ok=False)
    receipt = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "platform": platform.platform(), "python": sys.version, "cpu_count": os.cpu_count(),
               "commands": [], "candidate_invocations": 0, "auditor_invocations": 0, "retries": 0}
    started = time.perf_counter_ns()
    for name, script in [("candidate", "run_candidate.py"), ("auditor", "independent_audit.py")]:
        argv = [sys.executable, "-B", str(HERE / script), str(out / "rows")]
        receipt[name + "_invocations"] += 1
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        (out / (name + ".stdout.txt")).write_bytes(proc.stdout)
        (out / (name + ".stderr.txt")).write_bytes(proc.stderr)
        receipt["commands"].append({"argv": argv, "exit_code": proc.returncode})
        if proc.returncode:
            break
    receipt.update(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   elapsed_ns=time.perf_counter_ns() - started)
    (out / "execution.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return receipt["commands"][-1]["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
