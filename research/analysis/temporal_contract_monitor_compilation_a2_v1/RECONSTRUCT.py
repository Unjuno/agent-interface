import base64,gzip,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
items={
 "FORMAL_RESULT.json.gz.b64":("RESULT.reconstructed.json","218c16e336762068d874b57c6f6eef46de27e7d8cc3e89a5722190335cca3a4e"),
 "FORMAL_AUDIT.json.gz.b64":("AUDIT.reconstructed.json","326b44d4d987f66267e60f1622163de2f8c45af7f588baf3e09e7972051fa94c"),
}
for src,(dst,expected) in items.items():
 raw=gzip.decompress(base64.b64decode((R/src).read_text()))
 if hashlib.sha256(raw).hexdigest()!=expected: raise SystemExit(src)
 (R/dst).write_bytes(raw)
print("PASS_RECONSTRUCT")
