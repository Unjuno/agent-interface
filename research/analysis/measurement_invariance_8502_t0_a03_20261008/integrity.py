"""Candidate-side package integrity check. Auditor independently reimplements it."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXPECTED_SOURCES = {"README.md", "PROTOCOL.md", "CONSTRUCTION.md", "config.json", "generate.py", "candidate.py",
                    "integrity.py", "audit.py", "test_candidate.py", "test_audit.py", "freeze.py"}
EXPECTED_INPUTS = {"fixtures.json", "truth.json"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(directory: Path, freeze: dict) -> list[str]:
    errors = []
    if set(freeze.get("sources", {})) != EXPECTED_SOURCES:
        errors.append("sources:manifest_inventory")
    if set(freeze.get("inputs", {})) != EXPECTED_INPUTS:
        errors.append("inputs:manifest_inventory")
    if freeze.get("schema") != "issue8502-t0-a03-freeze-v1" or freeze.get("issue") != 8502 or freeze.get("allocation") != "A03":
        errors.append("freeze:identity")
    for category in ("sources", "inputs"):
        for name, expected in freeze.get(category, {}).items():
            path = directory / name
            if not path.is_file() or sha256(path.read_bytes()) != expected:
                errors.append(f"{category}:{name}")
    return errors


def load_json(directory: Path, name: str):
    return json.loads((directory / name).read_text(encoding="utf-8"))
