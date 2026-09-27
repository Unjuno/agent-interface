from __future__ import annotations
import base64,hashlib,json,lzma,tarfile,io,pathlib,sys
root=pathlib.Path(__file__).parent
meta=json.loads((root/'FORMAL_EVIDENCE.json').read_text())
b64=(root/'FORMAL_EVIDENCE.tar.xz.b64').read_text()
if hashlib.sha256(b64.encode()).hexdigest()!=meta['capsule_b64_sha256']: raise SystemExit('B64_HASH')
raw=base64.b64decode(b64)
if hashlib.sha256(raw).hexdigest()!=meta['capsule_sha256']: raise SystemExit('CAPSULE_HASH')
data=lzma.decompress(raw)
out=pathlib.Path(sys.argv[1])
if out.exists(): raise SystemExit('DEST_EXISTS')
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(data),mode='r:') as tf:
    members=tf.getmembers()
    if len(members)!=meta['files']: raise SystemExit('COUNT')
    for m in members:
        p=pathlib.PurePosixPath(m.name)
        if p.is_absolute() or '..' in p.parts or not m.isfile(): raise SystemExit('PATH')
        b=tf.extractfile(m).read()
        if hashlib.sha256(b).hexdigest()!=meta['members'].get(m.name): raise SystemExit('MEMBER_HASH')
        dest=out/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
print('PASS',len(members))
