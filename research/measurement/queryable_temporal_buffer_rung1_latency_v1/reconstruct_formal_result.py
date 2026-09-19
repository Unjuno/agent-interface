import base64,hashlib,json,lzma
from pathlib import Path
r=Path(__file__).parent
m=json.loads((r/'FORMAL_ARCHIVE.json').read_text())
b64=b''.join((r[x['name']]).read_bytes() for x in m['parts'])
for x in m['parts']:
    b=(r/x['name']).read_bytes(); assert len(b)==x['size'] and hashlib.sha256(b).hexdigest()==x['sha256']
xz=base64.b64decode(b64); assert len(xz)==m['xz_size'] and hashlib.sha256(xz).hexdigest()==m['xz_sha256']
raw=lzma.decompress(xz); assert len(raw)==m['raw_size'] and hashlib.sha256(raw).hexdigest()==m['raw_sha256']
(r/m['raw_name']).write_bytes(raw)
print(m['raw_sha256'])
