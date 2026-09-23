from pathlib import Path
import base64,gzip,hashlib,io,json,tarfile
r=Path(__file__).parent
m=json.loads((r/'ACTIVE_SOURCE_MANIFEST.json').read_text())
parts=[]
for x in m['chunks']:
    p=r/x['name']
    b=p.read_bytes()
    assert len(b)==x['chars']
    assert hashlib.sha256(b).hexdigest()==x['sha256']
    parts.append(b)
b64=b''.join(parts)
assert len(b64)==m['base64_bytes']
assert hashlib.sha256(b64).hexdigest()==m['base64_sha256']
a=base64.b64decode(b64)
assert len(a)==m['archive_bytes']
assert hashlib.sha256(a).hexdigest()==m['archive_sha256']
raw=gzip.decompress(a)
out=r/'active_reconstructed'
out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
    tf.extractall(out,filter='data')
for name,meta in m['files'].items():
    b=(out/name).read_bytes()
    assert len(b)==meta['bytes']
    assert hashlib.sha256(b).hexdigest()==meta['sha256']
print('PASS',len(m['files']))
