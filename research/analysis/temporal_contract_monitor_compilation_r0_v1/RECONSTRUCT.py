import base64,gzip,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
items={
 "FORMAL_RESULT.json.gz.b64":("RESULT.reconstructed.json","f487f29966fdcb6552d7f480985d3273ac7fcb4e6b7139e15640d7be957c56e5"),
 "FORMAL_AUDIT.json.gz.b64":("AUDIT.reconstructed.json","e744fd5e232b09a5912af1821f7816919c7c2390931436391c056c50bb26a0f8"),
}
for src,(dst,expected) in items.items():
 raw=gzip.decompress(base64.b64decode((R/src).read_text()))
 actual=hashlib.sha256(raw).hexdigest()
 if actual!=expected: raise SystemExit(f"{src}: {actual} != {expected}")
 (R/dst).write_bytes(raw)
print("PASS_RECONSTRUCT")
