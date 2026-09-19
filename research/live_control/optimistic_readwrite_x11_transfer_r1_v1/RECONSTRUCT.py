from pathlib import Path
import base64,gzip,hashlib,json
R=Path(__file__).resolve().parent
m=json.loads((R/'RETENTION.json').read_text())
b=(R/'FORMAL_ROWS.json.gz.b64').read_bytes()
assert hashlib.sha256(b).hexdigest()==m['base64_sha256']
g=base64.b64decode(b)
assert hashlib.sha256(g).hexdigest()==m['gzip_sha256']
r=gzip.decompress(g)
assert hashlib.sha256(r).hexdigest()==m['raw_sha256']
(R/'FORMAL_ROWS.json').write_bytes(r)
print(m['raw_sha256'])
