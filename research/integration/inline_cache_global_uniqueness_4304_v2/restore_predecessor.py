#!/usr/bin/env python3
"""Verify and safely restore the immutable allocation-01 source capsule."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent
CAPSULE = ROOT / "lineage" / "predecessor-v1"
MANIFEST = json.loads((CAPSULE / "SOURCE_PARTS.json").read_text("utf-8"))
EXPECTED_ARCHIVE_SHA256 = "634029b313aa5ba56daa22c87c16295fcce2983880b5d5776e819055e95075ac"
EXPECTED_ARCHIVE_BYTES = 17740


def git_blob_sha(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


parts: list[bytes] = []
for name, identity in sorted(MANIFEST["parts"].items()):
    data = (CAPSULE / name).read_bytes()
    if len(data) != identity["bytes"]:
        raise SystemExit(f"STOP_PART_LENGTH:{name}")
    if hashlib.sha256(data).hexdigest() != identity["sha256"]:
        raise SystemExit(f"STOP_PART_SHA256:{name}")
    if git_blob_sha(data) != identity["git_blob"]:
        raise SystemExit(f"STOP_PART_GIT_BLOB:{name}")
    parts.append(data)

encoded = b"".join(b"".join(part.split()) for part in parts)
archive = base64.b64decode(encoded, validate=True)
if len(archive) != EXPECTED_ARCHIVE_BYTES:
    raise SystemExit("STOP_ARCHIVE_LENGTH")
if hashlib.sha256(archive).hexdigest() != EXPECTED_ARCHIVE_SHA256:
    raise SystemExit("STOP_ARCHIVE_SHA256")

destination = Path(sys.argv[1]).resolve()
destination.mkdir(parents=True, exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(archive), mode="r:xz") as bundle:
    members = bundle.getmembers()
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"STOP_UNSAFE_MEMBER:{member.name}")
        if not (member.isdir() or member.isfile()):
            raise SystemExit(f"STOP_UNSUPPORTED_MEMBER:{member.name}")
    bundle.extractall(destination, members=members, filter="data")

print(json.dumps({
    "archive_bytes": len(archive),
    "archive_sha256": hashlib.sha256(archive).hexdigest(),
    "destination": str(destination),
    "members": [member.name for member in members],
    "parts_verified": len(parts),
}, sort_keys=True))
