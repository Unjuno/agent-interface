import datetime
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
start_utc = datetime.datetime.now(datetime.timezone.utc)
start_ns = time.perf_counter_ns()
proc = subprocess.run(
    [sys.executable, "-B", "composition_test.py"], cwd=ROOT,
    capture_output=True, text=True, encoding="utf-8", errors="replace")
end_ns = time.perf_counter_ns()
end_utc = datetime.datetime.now(datetime.timezone.utc)
raw = proc.stdout + proc.stderr
(ROOT / "results" / "RAW_COMPOSITION.txt").write_text(raw, encoding="utf-8")
receipt = {
    "schema": "map01-v39-release-cleanup-owner-queue-composition-run-v1",
    "command": [Path(sys.executable).name, "-B", "composition_test.py"],
    "cwd": ".",
    "start_utc": start_utc.isoformat(),
    "end_utc": end_utc.isoformat(),
    "elapsed_monotonic_ns": end_ns - start_ns,
    "exit_code": proc.returncode,
    "python_executable_basename": Path(sys.executable).name,
    "python_version": sys.version,
    "platform": platform.platform(),
    "source_refs": {
        "pr_7385_candidate": "23c228146a34ccaa71dafce153532703f04e4d23",
        "pr_7378_parent": "fbed929f629dabaa9ae752019d0ee7151d4d2298",
        "pr_7378_wrapper": "fbed929f629dabaa9ae752019d0ee7151d4d2298",
        "input_owner_v10": "13bab54ea6d91978247ecc1b70e5060db752367a",
    },
    "raw_path": "results/RAW_COMPOSITION.txt",
    "structured_path": "results/composition.json",
    "scope": "deterministic v10 owner-loop scheduling with mocked Xlib; no live allocation",
}
(ROOT / "RUN.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")
print(raw, end="")
if proc.returncode:
    raise SystemExit(proc.returncode)
