import base64,gzip,hashlib,io,tarfile,json
from pathlib import Path
p=Path('.')
m=json.loads((p/'SOURCE_MANIFEST.json').read_text())
gz=base64.b64decode((p/'source.b64').read_text().strip())
assert len(gz)==m['gzip_bytes']
assert hashlib.sha256(gz).hexdigest()==m['gzip_sha256']
raw=gzip.decompress(gz)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz' if False else 'r:') as t:
    t.extractall('reconstructed',filter='data')
print(m['gzip_sha256'])
