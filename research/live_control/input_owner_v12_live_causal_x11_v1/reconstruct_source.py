from pathlib import Path
import base64,gzip,hashlib,io,json,tarfile
r=Path(__file__).parent;m=json.loads((r/'SOURCE_MANIFEST.json').read_text())
b64=''.join((r[x['name']]).read_text().strip() for x in m['chunks']).encode()
assert hashlib.sha256(b64).hexdigest()==m['base64_sha256']
a=base64.b64decode(b64);assert hashlib.sha256(a).hexdigest()==m['archive_sha256']
out=r/'reconstructed_source';out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(gzip.decompress(a)),mode='r:') as tf: tf.extractall(out,filter='data')
for n,v in m['files'].items(): assert hashlib.sha256((out/n).read_bytes()).hexdigest()==v['sha256']
print('PASS',len(m['files']))
