#!/usr/bin/env python3
import hashlib,json,lzma,sys,tarfile
from pathlib import Path
here=Path(__file__).resolve().parent
meta=json.loads((here/"EVIDENCE_META.json").read_text())
raw=(here/"EVIDENCE.tar.xz").read_bytes()
if len(raw)!=meta["xz_bytes"] or hashlib.sha256(raw).hexdigest()!=meta["xz_sha256"]: raise SystemExit("xz mismatch")
tar=lzma.decompress(raw)
if len(tar)!=meta["tar_bytes"] or hashlib.sha256(tar).hexdigest()!=meta["tar_sha256"]: raise SystemExit("tar mismatch")
out=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/app-transport-drop-2802")
if out.exists(): raise SystemExit("refuse existing output")
out.mkdir(parents=True)
tmp=out/"evidence.tar"; tmp.write_bytes(tar)
with tarfile.open(tmp,"r:") as tf:
    for m in tf.getmembers():
        if m.name.startswith("/") or ".." in Path(m.name).parts: raise SystemExit("unsafe member")
    tf.extractall(out/"restored",filter="data")
for name,item in meta["files"].items():
    p=out/"restored"/name; data=p.read_bytes()
    if len(data)!=item["bytes"] or hashlib.sha256(data).hexdigest()!=item["sha256"]: raise SystemExit("member mismatch "+name)
print(meta["xz_sha256"])
