import base64,gzip,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parent
ITEMS={
 "FORMAL_RESULT.json.gz.b64":("RESULT.reconstructed.json","cf03b8cbf523c6c8bebf590028f6b16d20ae9c2a2ff7723451bd1dba356ebb60"),
 "FORMAL_AUDIT.json.gz.b64":("AUDIT.reconstructed.json","c13ec1ee3998c58384ee3a6c1d1c87a0814bb9f04703d0dc3b40de9383b04dd2"),
}
for src,(dst,expected) in ITEMS.items():
    raw=gzip.decompress(base64.b64decode((ROOT/src).read_text()))
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected: raise SystemExit(f"{src}: {actual} != {expected}")
    (ROOT/dst).write_bytes(raw)
print("PASS_RECONSTRUCT")
