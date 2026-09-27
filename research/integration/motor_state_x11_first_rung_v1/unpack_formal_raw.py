#!/usr/bin/env python3
import base64,hashlib,json,sys,tarfile,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
manifest=json.loads((here/"FORMAL_RAW_EXACT_MANIFEST.json").read_text())
encoded=(here/"FORMAL_RAW_EXACT.b64").read_bytes()
if len(encoded)!=manifest["base64_bytes"] or hashlib.sha256(encoded).hexdigest()!=manifest["base64_sha256"]: raise SystemExit("base64 mismatch")
raw=base64.b64decode(encoded)
if len(raw)!=manifest["decoded_bytes"] or hashlib.sha256(raw).hexdigest()!=manifest["decoded_sha256"]: raise SystemExit("archive mismatch")
out=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/motor-state-27-raw")
if out.exists(): raise SystemExit("refuse existing output")
out.mkdir(parents=True)
archive=out/"formal.tar.xz"; archive.write_bytes(raw)
with tarfile.open(archive,"r:xz") as tf:
 for m in tf.getmembers():
  if m.name.startswith("/") or ".." in Path(m.name).parts: raise SystemExit("unsafe member")
 tf.extractall(out/"restored",filter="data")
for item in manifest["members"]:
 p=out/"restored"/item["path"]; b=p.read_bytes()
 if len(b)!=item["bytes"] or hashlib.sha256(b).hexdigest()!=item["sha256"]: raise SystemExit("member mismatch "+item["path"])
print(manifest["decoded_sha256"])
