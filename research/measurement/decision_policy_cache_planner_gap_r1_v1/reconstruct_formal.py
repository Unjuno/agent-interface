from pathlib import Path
import base64,hashlib,lzma,json
p=Path(__file__).parent
m=json.loads((p/"FORMAL_ARCHIVE.json").read_text())
s="".join((p/x["name"]).read_text().strip() for x in m["parts"])
xz=base64.b64decode(s)
assert len(xz)==m["xz_bytes"]
assert hashlib.sha256(xz).hexdigest()==m["xz_sha256"]
raw=lzma.decompress(xz)
assert len(raw)==m["raw_bytes"]
assert hashlib.sha256(raw).hexdigest()==m["raw_sha256"]
(p/"FORMAL_RESULT.json").write_bytes(raw)
print(m["raw_sha256"])
