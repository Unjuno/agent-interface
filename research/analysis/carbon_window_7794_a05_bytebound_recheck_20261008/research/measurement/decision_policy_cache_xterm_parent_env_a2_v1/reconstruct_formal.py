from pathlib import Path
import hashlib,json,lzma
p=Path(__file__).resolve().parent
m=json.loads((p/"FORMAL_ARCHIVE.json").read_text())
xz=(p/"FORMAL_RESULT.json.xz").read_bytes()
assert len(xz)==m["archive_bytes"]
assert hashlib.sha256(xz).hexdigest()==m["archive_sha256"]
raw=lzma.decompress(xz)
assert len(raw)==m["raw_bytes"]
assert hashlib.sha256(raw).hexdigest()==m["raw_sha256"]
(p/"FORMAL_RESULT.json").write_bytes(raw)
print(m["raw_sha256"])
