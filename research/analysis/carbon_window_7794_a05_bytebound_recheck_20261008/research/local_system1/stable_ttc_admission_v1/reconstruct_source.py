#!/usr/bin/env python3
import base64,hashlib,json,tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
m=json.loads((root/"SOURCE_ARCHIVE.json").read_text())
b64="".join((root/p["name"]).read_text() for p in m["parts"])
raw=base64.b64decode(b64)
assert len(raw)==m["bytes"]
assert hashlib.sha256(raw).hexdigest()==m["sha256"]
out=root/"source.tar.xz"; out.write_bytes(raw)
with tarfile.open(out,"r:xz") as tf:
    for want in m["members"]:
        got=tf.extractfile(want["path"]).read()
        assert len(got)==want["bytes"]
        assert hashlib.sha256(got).hexdigest()==want["sha256"]
print("PASS source archive")
