#!/usr/bin/env python3
import base64, hashlib, json, sys, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if len(sys.argv)!=2: raise SystemExit("usage: restore_formal.py FRESH_DEST")
dest=Path(sys.argv[1])
if dest.exists(): raise SystemExit("destination exists")
m=json.loads((ROOT/"FORMAL_MANIFEST.json").read_text())
b64=(ROOT/"FORMAL_EVIDENCE.zlib.b64").read_bytes()
if hashlib.sha256(b64).hexdigest()!=m["base64_file_sha256"]: raise SystemExit("base64 file hash")
payload=b64.strip()
if len(payload)!=m["base64_chars"]: raise SystemExit("base64 length")
comp=base64.b64decode(payload,validate=True)
if len(comp)!=m["zlib_bytes"] or hashlib.sha256(comp).hexdigest()!=m["zlib_sha256"]: raise SystemExit("zlib identity")
raw=zlib.decompress(comp)
if len(raw)!=m["raw_container_bytes"] or hashlib.sha256(raw).hexdigest()!=m["raw_container_sha256"]: raise SystemExit("raw identity")
obj=json.loads(raw)
if obj.get("schema")!=m["schema"] or len(obj.get("files",{}))!=m["files_in_bundle"]: raise SystemExit("container schema")
dest.mkdir(parents=True)
for name,text in obj["files"].items():
    if "/" in name or name in {"",".",".."}: raise SystemExit("unsafe member")
    (dest/name).write_text(text)
for i,digest in enumerate(m["case_sha256"]):
    if hashlib.sha256((dest/f"case-{i:02d}.json").read_bytes()).hexdigest()!=digest: raise SystemExit(f"case hash {i}")
for name,digest in m["key_files"].items():
    if hashlib.sha256((dest/name).read_bytes()).hexdigest()!=digest: raise SystemExit("key hash "+name)
print(json.dumps({"restored":len(obj["files"]),"decision":json.loads((dest/"AUDIT.json").read_text())["decision"]},sort_keys=True))
