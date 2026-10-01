"""Run the frozen paired policy schedule using one child per measurement."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path


SOURCE = Path("/src")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def run(schedule_path, out_path):
    schedule_bytes = Path(schedule_path).read_bytes()
    schedule = json.loads(schedule_bytes)
    rows = []
    for size in schedule["sizes"]:
        block_data = schedule["sizes_data"][str(size)]
        candidates = block_data["candidates"]
        for block in block_data["blocks"]:
            for policy in block["policy_order"]:
                payload = json.dumps({"candidates": candidates}, sort_keys=True,
                                     separators=(",", ":"))
                start = time.perf_counter_ns()
                child = subprocess.run(
                    [sys.executable, "-B", str(SOURCE / "worker.py"), policy],
                    input=payload, text=True, encoding="utf-8", errors="strict",
                    capture_output=True, check=False,
                )
                wrapper_elapsed_ns = time.perf_counter_ns() - start
                try:
                    parsed = json.loads(child.stdout)
                    worker_cpu_ns = parsed.get("cpu_ns")
                    worker_wall_ns = parsed.get("wall_ns")
                    trace_sha256 = sha256(json.dumps(
                        parsed.get("trace"), separators=(",", ":")
                    ).encode("utf-8"))
                except (json.JSONDecodeError, AttributeError, TypeError):
                    worker_cpu_ns = None
                    worker_wall_ns = None
                    trace_sha256 = None
                rows.append({
                    "size": size,
                    "block": block["block"],
                    "policy": policy,
                    "exit": child.returncode,
                    "wrapper_elapsed_ns": wrapper_elapsed_ns,
                    "worker_cpu_ns": worker_cpu_ns,
                    "worker_wall_ns": worker_wall_ns,
                    "trace_sha256": trace_sha256,
                    "stdout_sha256": sha256(child.stdout.encode("utf-8")),
                    "stdout": child.stdout,
                    "stderr": child.stderr,
                })
    raw = {
        "schema": "scheduler-cost-scaling-raw-v1",
        "allocation": "scheduler-cost-scaling-2868-docker-desktop-x64-20260928-01",
        "schedule_sha256": sha256(schedule_bytes),
        "worker_count": len(rows),
        "rows": rows,
    }
    Path(out_path).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n",
                              encoding="utf-8", newline="\n")
    print(json.dumps({"status": "RUN_COMPLETE", "workers": len(rows),
                      "schedule_sha256": raw["schedule_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
