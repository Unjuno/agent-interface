#!/usr/bin/env python3
"""Create the immutable-input manifest for the one formal T0 invocation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
PROTOCOL = "issue-7993-t0-a01-v1"
FROZEN_SOURCES = [
    "PLAN.md",
    "candidate.py",
    "audit.py",
    "test_protocol.py",
    "run_experiment.py",
    "candidate_input.json",
    "oracle_input.json",
]
IMAGE = "python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = {
        "protocol": PROTOCOL,
        "source_sha256": {name: sha256(ROOT / name) for name in FROZEN_SOURCES},
        "environment": {
            "runtime": "WSLc 3.0.1.0",
            "image": IMAGE,
            "platform": "linux/amd64; Python 3.12.14",
            "network": "none",
            "cpus": 1,
            "memory_requested": "512M",
            "source_mount": "read-only",
            "output_mount": "separate read-write",
            "pull": "never",
        },
    }
    target = ROOT / "FROZEN.json"
    if target.exists():
        raise SystemExit("refusing to overwrite FROZEN.json")
    target.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"frozen": str(target), "source_count": len(FROZEN_SOURCES)}, sort_keys=True))


if __name__ == "__main__":
    main()
