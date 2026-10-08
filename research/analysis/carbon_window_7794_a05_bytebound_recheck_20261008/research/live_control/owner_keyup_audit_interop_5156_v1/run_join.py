"""Single construction-runner invocation for the frozen synthetic fixture."""
import hashlib
import json
import platform
import sys
from pathlib import Path

from normalize_join import normalize_join


ROOT = Path(__file__).parent
RESULTS = ROOT / "results" / "construction-01"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main():
    freeze = load("FREEZE.json")
    for name, expected in freeze["frozen_files_sha256"].items():
        actual = sha256(ROOT / name)
        if actual != expected:
            raise SystemExit(f"frozen_source_hash_mismatch:{name}")
    execution_freeze = load("EXECUTION_FREEZE.json")
    for name, expected in execution_freeze["sha256"].items():
        actual = sha256(ROOT / name)
        if actual != expected:
            raise SystemExit(f"execution_freeze_hash_mismatch:{name}")

    expected_inventory = load("expected_inventory.json")
    owner_rows = load("owner_rows_v1.json")
    caller_receipts = load("caller_receipts_v3.json")
    records = normalize_join(expected_inventory, owner_rows, caller_receipts)
    RESULTS.mkdir(parents=True, exist_ok=True)
    raw = {
        "schema": "owner-keyup-audit-interop-raw-v1",
        "records": records,
    }
    raw_path = RESULTS / "raw.json"
    raw_bytes = (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()
    raw_path.write_bytes(raw_bytes)
    receipt = {
        "allocation": freeze["allocation"],
        "runner_status": "PASS_JOIN_CONSTRUCTION_SYNTHETIC_ONLY",
        "command": "python -B run_join.py",
        "python": platform.python_version(),
        "base_main": freeze["base_main"],
        "pr_5298_head": freeze["pr_5298_head"],
        "pr_5415_head": freeze["pr_5415_head"],
        "execution_freeze_sha256": {
            name: value for name, value in execution_freeze["sha256"].items()
        },
        "runner_sha256": sha256(Path(__file__)),
        "normalize_join_sha256": sha256(ROOT / "normalize_join.py"),
        "input_sha256": {
            name: sha256(ROOT / name)
            for name in ("expected_inventory.json", "owner_rows_v1.json", "caller_receipts_v3.json")
        },
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest().upper(),
        "raw_record_count": len(records),
        "formal_x11_invocations": 0,
        "docker_or_orbstack_invocations": 0,
    }
    (RESULTS / "RUN.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": receipt["runner_status"],
                      "records": len(records), "raw_sha256": receipt["raw_sha256"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
