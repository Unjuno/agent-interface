import base64,hashlib,json
from pathlib import Path
r=Path(__file__).parent
m=json.loads((r/'FORMAL_ARCHIVE.json').read_text())
b64=b''
for p in m['parts']:
    b=(r/p['name']).read_bytes()
    assert len(b)==p['size'] and hashlib.sha256(b).hexdigest()==p['sha256']
    b64 += b
raw=base64.b64decode(b64)
assert len(raw)==m['raw_size'] and hashlib.sha256(raw).hexdigest()==m['raw_sha256']
(r/m['raw_name']).write_bytes(raw)
print(m['raw_sha256'])
