import base64,gzip,hashlib,json
from pathlib import Path
p=Path('.')
m=json.loads((p/'RESULT_MANIFEST.json').read_text());gz=base64.b64decode(''.join((p/x).read_text().strip() for x in m['parts']));assert len(gz)==m['gzip_bytes'] and hashlib.sha256(gz).hexdigest()==m['gzip_sha256'];raw=gzip.decompress(gz);assert len(raw)==m['raw_bytes'] and hashlib.sha256(raw).hexdigest()==m['raw_sha256'];(p/'FORMAL_RESULT.reconstructed.json').write_bytes(raw);print(m['raw_sha256'])
