import base64,gzip,hashlib,io,json,tarfile
from pathlib import Path
p=Path('.')
m=json.loads((p/'SOURCE_MANIFEST.json').read_text())
b64=''.join((p/x).read_text().strip() for x in m['parts'])
gz=base64.b64decode(b64);assert len(gz)==m['gzip_bytes'] and hashlib.sha256(gz).hexdigest()==m['gzip_sha256']
raw=gzip.decompress(gz);assert len(raw)==m['tar_bytes'] and hashlib.sha256(raw).hexdigest()==m['tar_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as t:t.extractall('reconstructed',filter='data')
for n,h in m['files'].items():assert hashlib.sha256((p/'reconstructed'/n).read_bytes()).hexdigest()==h
print(m['gzip_sha256'])
