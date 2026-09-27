#!/usr/bin/env python3
import hashlib,json,tarfile
from pathlib import Path
r=Path(__file__).resolve().parent
m=json.loads((r/"manifest.json").read_text())
p=r/m["archive"]["path"]
b=p.read_bytes()
assert len(b)==m["archive"]["bytes"]
assert hashlib.sha256(b).hexdigest()==m["archive"]["sha256"]
out=r/"reconstructed";out.mkdir(exist_ok=True)
with tarfile.open(p,"r:gz") as tf: tf.extractall(out)
print({"ok":True,"archive_sha256":m["archive"]["sha256"]})
