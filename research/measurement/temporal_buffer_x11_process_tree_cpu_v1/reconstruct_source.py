from pathlib import Path
import base64,gzip,tarfile,io,hashlib,json,sys
m=json.loads(Path('SOURCE_MANIFEST.json').read_text())
g=base64.b64decode(Path('source_bundle.tar.gz.b64').read_text())
assert len(g)==m['_bundle']['bytes'] and hashlib.sha256(g).hexdigest()==m['_bundle']['sha256']
raw=gzip.decompress(g); out=Path(sys.argv[1] if len(sys.argv)>1 else 'readback');out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as t:t.extractall(out)
for n,v in m.items():
    if n.startswith('_'):continue
    b=(out/n).read_bytes();assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'],n
print(m['_bundle']['sha256'])
