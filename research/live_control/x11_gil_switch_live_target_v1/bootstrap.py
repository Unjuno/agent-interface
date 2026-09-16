#!/usr/bin/env python3
import base64,hashlib,json,lzma,tarfile,io,pathlib
D=pathlib.Path(__file__).resolve().parent; m=json.loads((D/"freeze_manifest.json").read_text())
s="".join("".join((D/f"freeze.part{i:02d}.b64").read_text().split()) for i in range(m["chunks"]))
x=base64.b64decode(s); assert hashlib.sha256(x).hexdigest()==m["xz_sha256"]
t=lzma.decompress(x); assert hashlib.sha256(t).hexdigest()==m["tar_sha256"]
out=D/"restored_source"; out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(t),mode="r:") as tf: tf.extractall(out)
for n,v in m["files"].items(): assert hashlib.sha256((out/n).read_bytes()).hexdigest()==v["sha256"]
print("source bundle verified",len(m["files"]),"files")
