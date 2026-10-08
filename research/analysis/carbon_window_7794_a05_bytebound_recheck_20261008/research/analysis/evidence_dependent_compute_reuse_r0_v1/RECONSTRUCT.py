import base64,gzip,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
ITEMS={
 "FORMAL_RESULT.json.gz.b64":("RESULT.reconstructed.json","150cfce0c0d52125a1051cbcfd111b761cc926886a60658e2a159b1860a0d7a7"),
 "FORMAL_AUDIT.json.gz.b64":("AUDIT.reconstructed.json","6ece3fd756becd90d30fc114e049268f83b9bbf213a906323457daf541e036a6"),
}
for src,(dst,expected) in ITEMS.items():
    raw=gzip.decompress(base64.b64decode((ROOT/src).read_text()))
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=expected: raise SystemExit(f"{src}: {actual} != {expected}")
    (ROOT/dst).write_bytes(raw)
print("PASS_RECONSTRUCT")
