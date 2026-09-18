from pathlib import Path
import hashlib,lzma,json
p=Path(__file__).parent
m=json.loads((p/"FORMAL_ARCHIVE.json").read_text())
z=(p/"FORMAL_RESULT.json.xz").read_bytes()
assert len(z)==m["archive_bytes"]
assert hashlib.sha256(z).hexdigest()==m["archive_sha256"]
raw=lzma.decompress(z)
assert len(raw)==m["raw_bytes"]
assert hashlib.sha256(raw).hexdigest()==m["raw_sha256"]
(p/"RESULT.json").write_bytes(raw)
print(m["raw_sha256"])
