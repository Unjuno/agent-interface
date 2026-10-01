"""One deterministic T1 runner invocation; writes packet-level raw JSON."""
import hashlib
import json
import platform
import sys
from pathlib import Path

from transport_model import build_raw


ROOT = Path(__file__).parent
RESULTS = ROOT / "results" / "t1-01"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main():
    freeze = load("FREEZE.json")
    for name, expected in freeze["frozen_files_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise SystemExit(f"frozen_source_hash_mismatch:{name}")
    execution_freeze = load("EXECUTION_FREEZE.json")
    for name, expected in execution_freeze["sha256"].items():
        if sha256(ROOT / name) != expected:
            raise SystemExit(f"execution_freeze_hash_mismatch:{name}")
    if RESULTS.exists():
        raise SystemExit("results_path_exists; refusing to overwrite")

    raw = build_raw()
    RESULTS.mkdir(parents=True)
    raw_bytes = (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()
    raw_path = RESULTS / "raw.json"
    raw_path.write_bytes(raw_bytes)
    receipt = {
        "allocation": freeze["allocation"],
        "status": "RUN_COMPLETE_PENDING_INDEPENDENT_AUDIT",
        "command": "python -B run_t1.py",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "base_main": freeze["base_main"],
        "t0_raw_sha256": freeze["t0_raw_sha256"],
        "runner_sha256": sha256(Path(__file__)),
        "transport_model_sha256": sha256(ROOT / "transport_model.py"),
        "audit_source_sha256": sha256(ROOT / "audit_t1.py"),
        "execution_freeze_sha256": execution_freeze["sha256"],
        "trace_runs": len(raw["trace_runs"]),
        "fault_runs": len(raw["fault_runs"]),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest().upper(),
        "container_invocations": 0,
        "formal_or_live_gui_invocations": 0,
    }
    (RESULTS / "RUN.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": receipt["status"], "trace_runs": receipt["trace_runs"],
                      "fault_runs": receipt["fault_runs"], "raw_sha256": receipt["raw_sha256"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
