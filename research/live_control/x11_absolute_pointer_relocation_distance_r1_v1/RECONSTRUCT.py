from pathlib import Path
import base64,gzip,hashlib,json
R=Path(__file__).resolve().parent
m=json.loads((R/'RETENTION.json').read_text())
s=''.join((R/n).read_text() for n in m['base64_parts'])
for n in m['base64_parts']:
    assert hashlib.sha256((R/n).read_bytes()).hexdigest()==m['base64_part_sha256'][n]
gz=base64.b64decode(s)
assert hashlib.sha256(gz).hexdigest()==m['gzip_sha256']
raw=gzip.decompress(gz)
assert hashlib.sha256(raw).hexdigest()==m['raw_sha256']
(R/'FORMAL_ROWS.json').write_bytes(raw)
print(m['raw_sha256'])
