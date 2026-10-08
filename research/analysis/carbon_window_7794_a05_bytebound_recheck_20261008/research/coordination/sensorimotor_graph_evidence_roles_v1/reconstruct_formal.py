#!/usr/bin/env python3
from pathlib import Path
import gzip, hashlib

ROOT = Path(__file__).resolve().parent
GZ = ROOT / "formal-result.json.gz"
OUT = ROOT / "formal-result.json"
EXPECTED_GZ_SHA256 = "43d0d2aa6d69c6b5d5dc83394e4780321badc299dc7bb7ea2500acdae12c1509"
EXPECTED_RAW_SHA256 = "87dcf40010d132d0b422bd063fac0e33aed879250e90daf9370a1ace4fb04cb3"
EXPECTED_RAW_BYTES = 26532

assert hashlib.sha256(GZ.read_bytes()).hexdigest() == EXPECTED_GZ_SHA256
raw = gzip.decompress(GZ.read_bytes())
assert len(raw) == EXPECTED_RAW_BYTES
assert hashlib.sha256(raw).hexdigest() == EXPECTED_RAW_SHA256
OUT.write_bytes(raw)
print({"ok": True, "bytes": len(raw), "sha256": EXPECTED_RAW_SHA256})
