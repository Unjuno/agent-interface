from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALLOCATION = "needle-role-skill-lifecycle-4916-parity-diag-20260928-01"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    out = Path(os.environ["OUT_DIR"])
    out.mkdir(parents=True, exist_ok=True)
    freeze_bytes = (ROOT / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_bytes)
    source_hashes = {name: sha(ROOT / name) for name in freeze["sources"]}
    inputs = {name: sha(ROOT.parents[2] / path) for name, path in freeze["inputs"].items()}
    reference_hashes = {
        name: sha(ROOT.parents[2] / path)
        for name, path in freeze["reference_sources"].items()
    }
    receipt = {
        "allocation": ALLOCATION,
        "status": "RUNNING",
        "image_id": os.environ.get("CONTAINER_IMAGE_ID"),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "source_hashes": source_hashes,
        "reference_hashes": reference_hashes,
        "input_hashes": inputs,
    }
    if (
        source_hashes != freeze["sources"]
        or reference_hashes != freeze["reference_sources_sha256"]
        or inputs != freeze["inputs_sha256"]
    ):
        receipt["status"] = "STOP_HASH_MISMATCH"
        (out / "receipt.json").write_text(json.dumps(receipt, sort_keys=True) + "\n")
        return 2
    cmd = [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(ROOT), "-p", "test_parity_diag.py", "-v"]
    run = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    (out / "stdout.log").write_text(run.stdout, encoding="utf-8")
    (out / "stderr.log").write_text(run.stderr, encoding="utf-8")
    receipt.update({
        "command": cmd,
        "exit_code": run.returncode,
        "stdout_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(run.stderr.encode()).hexdigest(),
        "status": "PASS_ALL_12288_PARITY" if run.returncode == 0 else "FAIL_PARITY_DIAGNOSTIC",
    })
    (out / "receipt.json").write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"DIAGNOSTIC_STATUS={receipt['status']} EXIT={run.returncode}", flush=True)
    print(run.stderr, end="", flush=True)
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
