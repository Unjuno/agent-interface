#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, sys, tarfile
from pathlib import Path

PARTS = ['evidence.part00.b64', 'evidence.part01.b64', 'evidence.part02.b64', 'evidence.part03.b64', 'evidence.part04.b64', 'evidence.part05.b64', 'evidence.part06.b64', 'evidence.part07.b64', 'evidence.part08.b64', 'evidence.part09.b64', 'evidence.part10.b64', 'evidence.part11.b64', 'evidence.part12.b64', 'evidence.part13.b64', 'evidence.part14.b64', 'evidence.part15.b64', 'evidence.part16.b64', 'evidence.part17.b64', 'evidence.part18.b64', 'evidence.part19.b64']
ARCHIVE_SHA256 = "c7de104f6f57948540cd9bc27532193eac0f3c8e88bdabf2c8acbc3b70c6967d"
ARCHIVE_SIZE = 234064

def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_bundle.py FRESH_OUTPUT_DIR")
    here = Path(__file__).resolve().parent
    out = Path(sys.argv[1]).resolve()
    if out.exists():
        raise SystemExit(f"refusing existing output: {out}")
    out.mkdir(parents=True)
    archive = out / "evidence.tar.xz"
    h = hashlib.sha256(); total = 0
    with archive.open("wb") as dst:
        for name in PARTS:
            p = here / name
            data = base64.b64decode(p.read_text(encoding="ascii"), validate=True)
            dst.write(data); h.update(data); total += len(data)
    digest = h.hexdigest()
    if total != ARCHIVE_SIZE:
        raise SystemExit(f"archive size mismatch: {total} != {ARCHIVE_SIZE}")
    if digest != ARCHIVE_SHA256:
        raise SystemExit(f"archive sha256 mismatch: {digest}")
    with tarfile.open(archive, "r:xz") as tf:
        root = out.resolve()
        for member in tf.getmembers():
            target = (out / member.name).resolve()
            if target != root and root not in target.parents:
                raise SystemExit(f"unsafe archive path: {member.name}")
        tf.extractall(out, filter="data")
    print(f"PASS archive_bytes={total} sha256={digest}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
