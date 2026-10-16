"""Create the preregistration manifest exactly once; never run after formal start."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "5db548aa351c8ccd351831485d5e5940a4967ff3"
ALLOCATION = "UNJUNO-7993-VERIFIER-LABEL-MATURITY-T0-A02-MACOS-HOST-20261005"
FILES = [
    "README.md", "protocol.md", "preflight.json", "CONSTRUCTION_RECORD.md",
    "build_fixture.py", "candidate.py", "audit.py", "test_construction.py",
    "run_formal.py", "public_input.json", "auditor_truth.json", "prepare_freeze.py",
    "construction.normal.log", "construction.optimized.log", "construction.pycompile.log",
]

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def main() -> None:
    missing = [name for name in FILES if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit(f"missing freeze inputs: {missing}")
    manifest = {
        "allocation": ALLOCATION,
        "issue": 7993,
        "subgate": "T0-A02 exact superpopulation IPCW expectation",
        "base_commit": BASE,
        "branch": "research/7993-verifier-label-maturity-t0-a02-20261005",
        "package_path": "research/analysis/verifier_label_maturity_7993_t0_a02_20261005",
        "environment": {
            "host": platform.platform(), "machine": platform.machine(), "python": sys.version,
            "execution": "native host; one sequential low-priority process",
            "container": "none; host substitution",
            "network_enforcement": "none; no isolation claimed",
        },
        "formal_invocations_before_freeze": {"driver": 0, "candidate": 0, "auditor": 0},
        "files": {name: sha256(ROOT / name) for name in FILES},
    }
    target = ROOT / "FROZEN.json"
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o444)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"created": str(target), "sha256": sha256(target), "files": len(FILES)}, sort_keys=True))

if __name__ == "__main__":
    main()
