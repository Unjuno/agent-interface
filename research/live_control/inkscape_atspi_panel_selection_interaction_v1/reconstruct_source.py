#!/usr/bin/env python3
import base64,hashlib,json,lzma,tarfile,io
from pathlib import Path
r=Path(__file__).resolve().parent;m=json.loads((r/"source_manifest.json").read_text());s="".join("".join(p.read_text().split()) for p in sorted(r.glob("source.part*.b64")));xz=base64.b64decode(s,validate=True);assert len(xz)==m["xz_bytes"] and hashlib.sha256(xz).hexdigest()==m["xz_sha256"];tar=lzma.decompress(xz);assert len(tar)==m["tar_bytes"] and hashlib.sha256(tar).hexdigest()==m["tar_sha256"];out=r/"reconstructed_source";out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(tar),mode="r:") as tf:
    for x in tf.getmembers():
        assert x.name in m["files"] and "/" not in x.name and ".." not in x.name
        b=tf.extractfile(x).read();meta=m["files"][x.name];assert len(b)==meta["bytes"] and hashlib.sha256(b).hexdigest()==meta["sha256"];(out/x.name).write_bytes(b)
print({"ok":True,"files":len(m["files"]),"xz_sha256":m["xz_sha256"]})
