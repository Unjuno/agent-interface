#!/usr/bin/env python3
"""Verify and reconstruct the retained container/X11 bounded-recovery raw result."""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(root: Path) -> dict:
    manifest = json.loads((root / "raw-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != "container-x11-bounded-recovery-raw-manifest-v2":
        raise ValueError("unexpected manifest schema")

    packed = bytearray()
    verified_parts = []
    for item in manifest["parts"]:
        path = root / item["file"]
        data = path.read_bytes()
        actual = {
            "file": item["file"],
            "size": len(data),
            "sha256": sha256(data),
        }
        if actual["size"] != item["size"] or actual["sha256"] != item["sha256"]:
            raise ValueError(f"part mismatch: {item['file']}: {actual}")
        packed.extend(data)
        verified_parts.append(actual)

    packed_bytes = bytes(packed)
    if (
        len(packed_bytes) != manifest["packed_base64_size"]
        or sha256(packed_bytes) != manifest["packed_base64_sha256"]
    ):
        raise ValueError("packed base64 mismatch")

    try:
        compressed = base64.b64decode(packed_bytes, validate=True)
        raw = gzip.decompress(compressed)
    except Exception as exc:
        raise ValueError(f"decode/decompress failed: {exc}") from exc

    if (
        len(raw) != manifest["uncompressed_jsonl_size"]
        or sha256(raw) != manifest["uncompressed_jsonl_sha256"]
    ):
        raise ValueError("uncompressed raw mismatch")

    return {
        "verified": True,
        "part_count": len(verified_parts),
        "packed_base64_size": len(packed_bytes),
        "raw_size": len(raw),
        "raw_sha256": sha256(raw),
        "raw_nonempty_lines": sum(1 for line in raw.splitlines() if line),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.root), sort_keys=True))


if __name__ == "__main__":
    main()
