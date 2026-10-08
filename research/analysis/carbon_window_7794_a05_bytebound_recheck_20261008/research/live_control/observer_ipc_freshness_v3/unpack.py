#!/usr/bin/env python3
import base64,hashlib,json,pathlib,tarfile
r=pathlib.Path(__file__).resolve().parent
m=json.loads((r/"ARCHIVE.json").read_text())
b64=b"".join((r/p["name"]).read_bytes() for p in m["parts"])
for p in m["parts"]:
 q=r/p["name"]; assert q.stat().st_size==p["bytes"] and hashlib.sha256(q.read_bytes()).hexdigest()==p["sha256"]
data=base64.b64decode(b64,validate=True)
assert len(data)==m["archive_bytes"] and hashlib.sha256(data).hexdigest()==m["archive_sha256"]
out=r/"restored"; out.mkdir(exist_ok=False)
arc=r/"_evidence.tar.xz"; arc.write_bytes(data)
with tarfile.open(arc,"r:xz") as tf:
 for member in tf.getmembers():
  p=pathlib.PurePosixPath(member.name)
  if member.issym() or member.islnk() or member.name.startswith("/") or ".." in p.parts: raise ValueError("unsafe member")
 tf.extractall(out)
arc.unlink()
print(m["archive_sha256"],len(data),out)
