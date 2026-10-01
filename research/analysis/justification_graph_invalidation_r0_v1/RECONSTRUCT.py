import base64,gzip,hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parent
ITEMS={
 "FORMAL_RESULT.json.gz.b64":("RESULT.reconstructed.json","dcea4e3bb60a477f4e796a5ace42122b878df2a19f996e864c5937de7d9fc478"),
 "FORMAL_AUDIT.json.gz.b64":("AUDIT.reconstructed.json","4fcaec2963ff8fd677297b90f21b5c7d7824233d83311908d1439c18e5f59a1f"),
}
for src,(dst,expected) in ITEMS.items():
    raw=gzip.decompress(base64.b64decode((ROOT/src).read_text()))
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected: raise SystemExit(f"{src}: {actual} != {expected}")
    (ROOT/dst).write_bytes(raw)
print("PASS_RECONSTRUCT")
