"""Freeze the final packet file hashes after logs and report are retained."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
manifest_path = HERE / "manifest.json"
entries = {}
for path in sorted(HERE.rglob("*")):
    if path.is_file() and path != manifest_path:
        entries[path.relative_to(HERE).as_posix()] = hashlib.sha256(
            path.read_bytes()).hexdigest()
manifest_path.write_text(json.dumps({
    "schema": "agent-interface-evidence-manifest-v1",
    "entries": entries,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"manifest_entries": len(entries)}, sort_keys=True))
