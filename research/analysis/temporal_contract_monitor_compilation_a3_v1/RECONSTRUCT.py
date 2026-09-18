import base64,gzip,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
items={
 "FORMAL_RESULT.json.gz.b64":("RESULT.reconstructed.json","26d1bd2b9cc65430d5ddb1c84cd4cc1b94a6d1759ee7e413aa838b3d14e7a904"),
 "FORMAL_AUDIT.json.gz.b64":("AUDIT.reconstructed.json","5ee694c6201b910105827c337534003ab162a354f7b3f251891e3a270942605d"),
}
for src,(dst,expected) in items.items():
 raw=gzip.decompress(base64.b64decode((R/src).read_text()))
 if hashlib.sha256(raw).hexdigest()!=expected: raise SystemExit(src)
 (R/dst).write_bytes(raw)
print("PASS_RECONSTRUCT")
