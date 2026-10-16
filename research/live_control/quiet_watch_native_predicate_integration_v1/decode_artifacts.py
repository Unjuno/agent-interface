#!/usr/bin/env python3
import base64, gzip, hashlib, zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
RAW_SHA256="07533a59ab969f3cbde6bb40a4f244d2146d79698c3af179424de3e6b87a0599"
ZLIB_SHA256="cfcb335fd4a482ae6be31e6bcbe462cc6fc24f45b53b1415d468a24a70316868"
PARTS=['raw.json.zlib.b64.part00', 'raw.json.zlib.b64.part01', 'raw.json.zlib.b64.part02', 'raw.json.zlib.b64.part03', 'raw.json.zlib.b64.part04', 'raw.json.zlib.b64.part05', 'raw.json.zlib.b64.part06', 'raw.json.zlib.b64.part07']
BINARIES={
 "native_acquire.so": "e4e9262ec553f1244d3e781caddb496ae1ac9dae0607451e3cf75422e07305bc",
 "native_predicate.so": "fb091f2997882c664e740d90c8f5f1c8a8f64d86410ede851a08105aa01e1d3d",
}
def h(b): return hashlib.sha256(b).hexdigest()
b64=''.join((HERE/p).read_text(encoding='ascii') for p in PARTS)
z=base64.b64decode(b64)
assert h(z)==ZLIB_SHA256, (h(z), ZLIB_SHA256)
raw=zlib.decompress(z)
assert h(raw)==RAW_SHA256, (h(raw), RAW_SHA256)
(HERE/'raw.json').write_bytes(raw)
for name, expected in BINARIES.items():
    comp=base64.b64decode((HERE/(name+'.gz.b64')).read_text(encoding='ascii'))
    data=gzip.decompress(comp)
    assert h(data)==expected, (name,h(data),expected)
    (HERE/name).write_bytes(data)
print('PASS', RAW_SHA256, len(raw), len(PARTS))
