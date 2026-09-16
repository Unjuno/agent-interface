#!/usr/bin/env python3
from pathlib import Path
import base64,hashlib,io,json,lzma,tarfile
D=Path(__file__).resolve().parent
m=json.loads((D/"result_publication_manifest_v3.json").read_text())
s="".join("".join((D/p["path"]).read_text().split()) for p in m["canonical_parts"])
x=base64.b64decode(s)
assert len(x)==m["bundle_xz_bytes"] and hashlib.sha256(x).hexdigest()==m["bundle_xz_sha256"]
t=lzma.decompress(x)
assert len(t)==m["bundle_tar_bytes"] and hashlib.sha256(t).hexdigest()==m["bundle_tar_sha256"]
out=D/"restored_result_bundle_v3"; out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(t),mode="r:") as tf: tf.extractall(out)
for n,v in m["files"].items():
    b=(out/n).read_bytes(); assert len(b)==v["bytes"] and hashlib.sha256(b).hexdigest()==v["sha256"]
raw=lzma.decompress((out/"raw.json.xz").read_bytes())
assert len(raw)==m["formal_raw_bytes"] and hashlib.sha256(raw).hexdigest()==m["formal_raw_sha256"]
print("canonical v3 verified",len(raw),hashlib.sha256(raw).hexdigest())
