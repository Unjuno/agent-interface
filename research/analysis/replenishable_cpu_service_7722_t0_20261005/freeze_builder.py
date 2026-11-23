#!/usr/bin/env python3
"""Build the immutable T0 freeze after source and trace preparation."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()

source_hashes = {
    "candidate_sha256": sha("candidate.py"),
    "auditor_sha256": sha("auditor.py"),
    "cases_sha256": sha("cases.json"),
    "protocol_sha256": sha("PROTOCOL.md"),
    "freeze_builder_sha256": sha("freeze_builder.py"),
}
image = "python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016"
freeze = {
    "allocation_id": "CPU-CONTROL-7722-T0-20261005-01",
    "issue": 7722,
    "source_base": "3dbbda05eb8d5067ee2c2969615e472a0f20f562",
    "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "runtime": "WSLc",
    "wslc_version": "3.0.1.0",
    "image": image,
    "image_id": "sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364",
    "image_architecture": "amd64",
    "network": "none",
    "cpu_request": "1",
    "memory_request": "256m",
    "memory_enforcement": "unverified; preserve emitted warnings",
    "gpu": "none",
    "candidate_invocations": 1,
    "auditor_invocations": 1,
    "retries": 0,
    "seed_method": "CPython random.Random(seed).randint(400,600), one RNG instance per seed",
    "protocol_sha256": source_hashes["protocol_sha256"],
    "source_hashes": source_hashes,
    "source_names": {
        "candidate": "candidate.py", "auditor": "auditor.py", "cases": "cases.json",
        "protocol": "PROTOCOL.md", "freeze_builder": "freeze_builder.py"
    }
}
(ROOT / "freeze.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"freeze": str(ROOT / "freeze.json"), "sources": source_hashes}, sort_keys=True))
