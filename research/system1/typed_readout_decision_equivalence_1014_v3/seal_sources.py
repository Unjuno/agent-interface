#!/usr/bin/env python3
"""Hash frozen source and construction inputs; excludes formal outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "SOURCE_MANIFEST.json"
EXCLUDED = {"SOURCE_MANIFEST.json", "FORMAL_FREEZE.json", "RESULTS_MANIFEST.json"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


files = sorted(p for p in ROOT.rglob("*") if p.is_file()
               and p.name not in EXCLUDED and "__pycache__" not in p.parts
               and "formal" not in p.relative_to(ROOT).parts)
entries = [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
            "sha256": sha256(p)} for p in files]
tree = hashlib.sha256("".join(f"{x['sha256']}  {x['path']}\n" for x in entries).encode()).hexdigest()
payload = {"root": "research/system1/typed_readout_decision_equivalence_1014_v3",
           "algorithm": "SHA-256", "files": entries, "tree_sha256": tree}
OUT.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"files": len(entries), "tree_sha256": tree}, sort_keys=True))
