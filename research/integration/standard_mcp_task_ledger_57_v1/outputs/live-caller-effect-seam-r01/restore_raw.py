from __future__ import annotations
import base64
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parent
for row in (root / "SHA256SUMS").read_text(encoding="ascii").splitlines():
    digest, relative = row.split("  ", 1)
    encoded = (root / (relative + ".b64")).read_bytes().strip()
    payload = base64.b64decode(encoded, validate=True)
    if hashlib.sha256(payload).hexdigest() != digest:
        raise SystemExit(f"digest mismatch: {relative}")
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
print("verified raw outputs")
