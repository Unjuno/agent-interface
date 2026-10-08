from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def sample(container: str) -> dict:
    stamp = time.time_ns()
    smi = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=5,
    )
    ps = subprocess.run(["docker", "exec", container, "ollama", "ps"], capture_output=True, text=True, timeout=8)
    used = util = None
    try:
        used, util = [int(v.strip()) for v in smi.stdout.strip().splitlines()[0].split(",")]
    except (IndexError, ValueError):
        pass
    return {
        "utc_ns": stamp,
        "utc": datetime.fromtimestamp(stamp / 1e9, tz=timezone.utc).isoformat(),
        "nvidia_smi_exit": smi.returncode,
        "nvidia_smi_stdout": smi.stdout,
        "nvidia_smi_stderr": smi.stderr,
        "memory_used_mib": used,
        "gpu_utilization_percent": util,
        "ollama_ps_exit": ps.returncode,
        "ollama_ps_stdout": ps.stdout,
        "ollama_ps_stderr": ps.stderr,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--container", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--stop-file", type=Path, required=True)
    p.add_argument("--interval", type=float, default=0.20)
    args = p.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a", encoding="utf-8", newline="\n") as f:
        while not args.stop_file.exists():
            row = sample(args.container)
            f.write(json.dumps(row, sort_keys=True) + "\n")
            f.flush()
            time.sleep(args.interval)


if __name__ == "__main__":
    main()

