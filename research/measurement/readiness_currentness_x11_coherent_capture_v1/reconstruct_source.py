#!/usr/bin/env python3
import base64,gzip,json,sys
from pathlib import Path
root=Path(__file__).resolve().parent
parts=[]
for p in sorted(root.glob("source_archive.b64.*")):
    parts.append(p.read_text().strip())
obj=json.loads(gzip.decompress(base64.b64decode("".join(parts))).decode())
out=Path(sys.argv[1] if len(sys.argv)>1 else root/"reconstructed")
out.mkdir(parents=True,exist_ok=True)
for name,content in obj.items():
    (out/name).write_text(content)
print(out)
