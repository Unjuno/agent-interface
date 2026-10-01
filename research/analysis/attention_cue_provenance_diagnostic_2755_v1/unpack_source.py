from __future__ import annotations
import base64,gzip,hashlib,io,json,pathlib,tarfile,sys
root=pathlib.Path(__file__).parent
meta=json.loads((root/'FREEZE.json').read_text())
b64=(root/'SOURCE_CAPSULE.tar.gz.b64').read_text()
if hashlib.sha256(b64.encode()).hexdigest()!=meta['source_capsule_b64_sha256']: raise SystemExit('B64_HASH')
raw=base64.b64decode(b64)
if hashlib.sha256(raw).hexdigest()!=meta['source_capsule_sha256']: raise SystemExit('CAPSULE_HASH')
data=gzip.decompress(raw)
out=pathlib.Path(sys.argv[1])
if out.exists(): raise SystemExit('DEST_EXISTS')
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(data),mode='r:') as tf:
    members=tf.getmembers()
    if len(members)!=len(meta['files']): raise SystemExit('COUNT')
    for m in members:
        p=pathlib.PurePosixPath(m.name)
        if p.is_absolute() or '..' in p.parts or not m.isfile(): raise SystemExit('PATH')
        b=tf.extractfile(m).read()
        exp=meta['files'].get(m.name,{}).get('sha256')
        if not exp or hashlib.sha256(b).hexdigest()!=exp: raise SystemExit('MEMBER_HASH')
        (out/p).write_bytes(b)
print('PASS',len(members))
