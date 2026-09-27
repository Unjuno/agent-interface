#!/usr/bin/env python3
"""Create a content-only manifest for a locally mounted model snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("model", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    files = sorted(p for p in args.model.rglob("*") if p.is_file())
    result = {
        "repo_id": "Qwen/Qwen2.5-0.5B-Instruct",
        "revision": "7ae557604adf67be50417f59c2c2f167def9a775",
        "files": [{"path": str(p.relative_to(args.model)).replace("\\", "/"),
                   "size": p.stat().st_size, "sha256": digest(p)} for p in files],
        "total_bytes": sum(p.stat().st_size for p in files),
    }
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(files), "total_bytes": result["total_bytes"]}, sort_keys=True))


if __name__ == "__main__":
    main()
