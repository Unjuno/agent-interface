import base64,hashlib,json,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent
m=json.loads((H/"PUBLICATION_MANIFEST.json").read_text())
chunks=[]
for x in m["parts"]:
 p=H/x["name"]; b=p.read_bytes(); assert len(b)==x["bytes"]; assert hashlib.sha256(b).hexdigest()==x["sha256"]; chunks.append(b)
b64=b"".join(chunks); assert hashlib.sha256(b64).hexdigest()==m["archive_concat_sha256"]
raw=base64.b64decode(b64); assert hashlib.sha256(raw).hexdigest()==m["archive_binary_sha256"]
p=H/"SOURCE_ARCHIVE.tar.gz"; p.write_bytes(raw)
with tarfile.open(p,"r:gz") as t: t.extractall(H/"reconstructed")
print("PASS_RECONSTRUCT", len(list((H/"reconstructed").iterdir())))
