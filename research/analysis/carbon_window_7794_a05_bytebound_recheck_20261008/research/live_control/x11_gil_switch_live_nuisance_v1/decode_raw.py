#!/usr/bin/env python3
import base64, hashlib, lzma
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW_SHA256 = "5fa5c329ad129320e934a6ed7eccac42e9365403d86152bd31f9893348dc5121"
XZ_SHA256 = "74702152788b155cf893b466e1dfca2eab786745de20df6c79062a0ce259715a"

parts = sorted(HERE.glob("raw.part*.b64"), key=lambda p: p.name)
text = "".join("".join(p.read_text().split()) for p in parts)
xz = base64.b64decode(text, validate=True)
assert len(xz) == 91440
assert hashlib.sha256(xz).hexdigest() == XZ_SHA256
raw = lzma.decompress(xz)
assert len(raw) == 1113523
assert hashlib.sha256(raw).hexdigest() == RAW_SHA256
(HERE / "raw.json").write_bytes(raw)
print({"parts": len(parts), "xz_bytes": len(xz), "raw_bytes": len(raw), "xz_sha256": XZ_SHA256, "raw_sha256": RAW_SHA256})
