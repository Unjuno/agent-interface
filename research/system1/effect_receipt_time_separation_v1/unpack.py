#!/usr/bin/env python3
import argparse,base64,hashlib,json,pathlib,zlib
ap=argparse.ArgumentParser(); ap.add_argument("out"); a=ap.parse_args(); out=pathlib.Path(a.out)
if out.exists(): raise SystemExit("destination exists")
p=json.loads(pathlib.Path("PACK.json").read_text()); chunks=[]
for part in p["parts"]:
 b=pathlib.Path(part["name"]).read_bytes()
 if hashlib.sha256(b).hexdigest()!=part["sha256"]: raise SystemExit("part hash mismatch")
 chunks.append(b.decode().strip())
enc="".join(chunks); raw=zlib.decompress(base64.b64decode(enc))
if hashlib.sha256(raw).hexdigest()!=p["decoded_sha256"]: raise SystemExit("decoded hash mismatch")
obj=json.loads(raw)
if len(obj)!=p["files"]: raise SystemExit("file count mismatch")
out.mkdir()
for rel,e in obj.items():
 q=pathlib.PurePosixPath(rel)
 if q.is_absolute() or ".." in q.parts: raise SystemExit("unsafe path")
 b=base64.b64decode(e["b64"])
 if hashlib.sha256(b).hexdigest()!=e["sha256"]: raise SystemExit("member hash mismatch")
 dst=out/pathlib.Path(*q.parts); dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(b)
print(json.dumps({"files":len(obj),"decoded_sha256":p["decoded_sha256"]},sort_keys=True))
