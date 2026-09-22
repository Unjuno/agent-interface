#!/usr/bin/env python3
import hashlib, json, sys
from pathlib import Path

here = Path(__file__).resolve().parent
manifest = json.loads((here / "PATCH_MANIFEST.json").read_text())
out = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/activation-hit-target-4036-additive.patch")
if out.exists():
    raise SystemExit(f"refuse existing output: {out}")
with out.open("wb") as dst:
    for item in manifest["parts"]:
        raw = (here / "full_patch" / item["name"]).read_bytes()
        if not raw:
            raise SystemExit(f"empty part: {item['name']}")
        dst.write(raw)
raw = out.read_bytes()
if len(raw) != manifest["source_bytes"]:
    raise SystemExit(f"byte count mismatch: {len(raw)}")
digest = hashlib.sha256(raw).hexdigest()
if digest != manifest["source_sha256"]:
    raise SystemExit(f"sha256 mismatch: {digest}")
if raw.count(b"\n") != manifest["source_lines"]:
    raise SystemExit(f"line count mismatch: {raw.count(b'\n')}")
print(f"{out} {len(raw)} bytes sha256={digest}")
