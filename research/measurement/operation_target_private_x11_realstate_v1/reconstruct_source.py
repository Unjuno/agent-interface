from pathlib import Path
import base64,hashlib,tarfile,json,io
raw=base64.b64decode(Path('source_bundle.tar.b64').read_text())
man=json.loads(Path('SOURCE_MANIFEST.json').read_text())
assert hashlib.sha256(raw).hexdigest()==man['archive_sha256']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as t:t.extractall('reconstructed_source')
for name,meta in man['members'].items():
 b=(Path('reconstructed_source')/name).read_bytes(); assert len(b)==meta['bytes'] and hashlib.sha256(b).hexdigest()==meta['sha256'], name
print(man['archive_sha256'])
