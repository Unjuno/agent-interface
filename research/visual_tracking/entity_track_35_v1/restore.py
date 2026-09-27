#!/usr/bin/env python3
import base64, hashlib, json, lzma, tarfile, io, sys
from pathlib import Path
root=Path(__file__).resolve().parent
out=Path(sys.argv[1])
if out.exists(): raise SystemExit('destination exists')
manifest=json.loads((root/'EVIDENCE.json').read_text())
b64=''.join((root/n).read_text().strip() for n in manifest['parts'])
xz=base64.b64decode(b64)
if hashlib.sha256(xz).hexdigest()!=manifest['xz_sha256']: raise SystemExit('archive hash')
raw=lzma.decompress(xz)
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
    members=tf.getmembers()
    if len(members)!=manifest['member_count']: raise SystemExit('member count')
    for m in members:
        if not m.isfile() or m.name.startswith('/') or '..' in Path(m.name).parts: raise SystemExit('unsafe member')
        p=out/m.name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(tf.extractfile(m).read())
print(json.dumps({'members':len(members),'xz_sha256':manifest['xz_sha256']},sort_keys=True))
