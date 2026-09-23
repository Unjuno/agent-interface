from pathlib import Path
import base64,gzip,hashlib,io,json,tarfile
r=Path(__file__).parent
m=json.loads((r/'SOURCE_MANIFEST_V2.json').read_text())
b64=''.join((r/x['name']).read_text().strip() for x in m['chunks']).encode()
assert len(b64)==m['base64_bytes']
assert hashlib.sha256(b64).hexdigest()==m['base64_sha256']
raw=base64.b64decode(b64)
assert len(raw)==m['archive_bytes']
assert hashlib.sha256(raw).hexdigest()==m['archive_sha256']
payload=gzip.decompress(raw)
out=r/'reconstructed_source_v2'; out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(payload),mode='r:') as tf: tf.extractall(out,filter='data')
for n,v in m['files'].items():
    p=out/n
    assert len(p.read_bytes())==v['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256'],n
print('PASS',len(m['files']))
