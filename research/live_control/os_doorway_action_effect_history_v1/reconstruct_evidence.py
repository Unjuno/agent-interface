#!/usr/bin/env python3
import base64, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARTS = [ROOT / f"evidence.base64.part-{i:02d}" for i in range(7)]
EXPECTED_PART_SHA256 = [
    "6c2a4e9dc8f9cb9db41ccaec4a0ad43e1f20bd4185fa009b7c275cad4e1f7f21",
    "2d5dfba4bb9063b328b179ff2f424a2168076b58571eceb5b7eb9e27f5bbf008",
    "41d197038b327406956b0bbd3fd889184f0b418c7208ed258a4a80270dc917b2",
    "44d120376475075b52af8b94d3907a8d60214d7134a3ed3d6a888ae4ea73cc70",
    "0f25fdb13656ea820f60d0c91c50d01400fef4439d714a040e0c064e0b7afa4c",
    "7fc0ee0d00147c73db2b379a11afa90a8b2f28af0aade50f903ba427de00a69c",
    "8323b1c2538f546a357b914e0d536957511752f635d2c031de14e977a2583295",
]
EXPECTED_ARCHIVE_SHA256 = "49af2549e903db16f691863a881f545f9f36f1f039f71b16f985b09aeb7fe9ea"
EXPECTED_ARCHIVE_SIZE = 15420
OUT = ROOT / "os_doorway_action_effect_history_v1_evidence.tar.xz"

chunks = []
for path, expected in zip(PARTS, EXPECTED_PART_SHA256):
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise SystemExit(f"part hash mismatch: {path.name}: {actual} != {expected}")
    chunks.append(raw.decode("ascii").strip())
archive = base64.b64decode("".join(chunks), validate=True)
if len(archive) != EXPECTED_ARCHIVE_SIZE:
    raise SystemExit(f"archive size mismatch: {len(archive)} != {EXPECTED_ARCHIVE_SIZE}")
actual_archive = hashlib.sha256(archive).hexdigest()
if actual_archive != EXPECTED_ARCHIVE_SHA256:
    raise SystemExit(f"archive hash mismatch: {actual_archive} != {EXPECTED_ARCHIVE_SHA256}")
OUT.write_bytes(archive)
print(f"PASS {OUT.name} bytes={len(archive)} sha256={actual_archive}")
