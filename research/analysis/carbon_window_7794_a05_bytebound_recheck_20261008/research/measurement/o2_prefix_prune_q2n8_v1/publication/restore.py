"""Read-only extractor for Issue #4423 split compact evidence; executes no study."""
from __future__ import annotations
import base64, hashlib, io, json, pathlib, sys, tarfile
here = pathlib.Path(__file__).resolve().parent
meta = json.loads((here/'PUBLICATION.json').read_text())
out = pathlib.Path(sys.argv[1]).resolve()
if out.exists():
    raise SystemExit('destination exists')
chunks=[]
for row in meta['parts']:
    p=here/row['name']
    data=p.read_bytes()
    if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:
        raise SystemExit(f"part mismatch: {row['name']}")
    chunks.append(data)
encoded=b''.join(b''.join(chunks).split())
blob=base64.b64decode(encoded, validate=True)
if len(blob)!=meta['compact_archive_bytes'] or hashlib.sha256(blob).hexdigest()!=meta['compact_archive_sha256']:
    raise SystemExit('archive mismatch')
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(blob), mode='r:xz') as tf:
    members=tf.getmembers()
    for m in members:
        target=(out/m.name).resolve()
        if target!=out and out not in target.parents:
            raise SystemExit('unsafe path')
        if m.issym() or m.islnk():
            raise SystemExit('links forbidden')
    tf.extractall(out)
print(json.dumps({'decision':'PASS_COMPACT_RESTORE','members':len(members),'sha256':meta['compact_archive_sha256']},sort_keys=True))
