import base64,gzip,hashlib,io,json,tarfile
from pathlib import Path
p=Path('.')
m=json.loads((p/'SOURCE_MANIFEST.json').read_text())
gz=base64.b64decode((p/'source.tar.gz.b64').read_text())
assert len(gz)==m['gzip_bytes'] and hashlib.sha256(gz).hexdigest()==m['gzip_sha256']
raw=gzip.decompress(gz)
assert len(raw)==m['tar_bytes'] and hashlib.sha256(raw).hexdigest()==m['tar_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as t:t.extractall('reconstructed',filter='data')
for n,h in m['members'].items():assert hashlib.sha256((p/'reconstructed'/n).read_bytes()).hexdigest()==h
print(m['gzip_sha256'])
