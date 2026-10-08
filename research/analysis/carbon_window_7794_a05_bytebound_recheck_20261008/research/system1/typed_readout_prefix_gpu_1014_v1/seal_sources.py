#!/usr/bin/env python3
"""Hash the additive evidence package, excluding only this generated manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "SOURCE_MANIFEST.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


files = sorted(p for p in ROOT.rglob("*") if p.is_file() and p != OUT)
entries = [{"path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "bytes": p.stat().st_size, "sha256": sha256(p)} for p in files]
payload = {"root": "research/system1/typed_readout_prefix_gpu_1014_v1",
           "files": entries,
           "tree_sha256": hashlib.sha256(
               "".join(f"{x['sha256']}  {x['path']}\n" for x in entries).encode()
           ).hexdigest()}
OUT.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"files": len(entries), "tree_sha256": payload["tree_sha256"]}, sort_keys=True))
