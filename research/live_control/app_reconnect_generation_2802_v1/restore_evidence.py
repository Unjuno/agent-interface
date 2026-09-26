#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
h=Path(__file__).resolve().parent
m=json.loads((h/"EVIDENCE_PARTS.json").read_text())
out=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/app-reconnect-generation-2802-evidence.tar.xz")
if out.exists(): raise SystemExit("refuse existing output")
chunks=[]
for item in m["parts"]:
 b=(h/item["name"]).read_bytes()
 if len(b)!=item["bytes"] or hashlib.sha256(b).hexdigest()!=item["sha256"]: raise SystemExit(item["name"]+" mismatch")
 chunks.append(b)
raw=b"".join(chunks)
if len(raw)!=m["combined_bytes"] or hashlib.sha256(raw).hexdigest()!=m["combined_sha256"]: raise SystemExit("combined mismatch")
out.write_bytes(raw)
print(m["combined_sha256"])
