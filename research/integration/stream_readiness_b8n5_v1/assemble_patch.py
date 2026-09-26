#!/usr/bin/env python3
import hashlib, json, pathlib
root=pathlib.Path(__file__).resolve().parent
m=json.loads((root/"PATCH_MANIFEST.json").read_text())
chunks=[]
for p in m["parts"]:
    b=(root/p["name"]).read_bytes()
    if hashlib.sha256(b).hexdigest()!=p["sha256"]:
        raise SystemExit("part SHA-256 mismatch: "+p["name"])
    chunks.append(b)
raw=b"".join(chunks)
if len(raw)!=m["full_patch"]["bytes"] or hashlib.sha256(raw).hexdigest()!=m["full_patch"]["sha256"]:
    raise SystemExit("full patch identity mismatch")
out=root/"stream-readiness-b8n5.patch"
out.write_bytes(raw)
print(json.dumps({"bytes":len(raw),"lines":raw.count(b"\\n"),"sha256":hashlib.sha256(raw).hexdigest()},sort_keys=True))
