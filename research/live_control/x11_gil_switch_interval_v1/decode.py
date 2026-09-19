#!/usr/bin/env python3
import base64,hashlib,lzma
from pathlib import Path
HERE=Path(__file__).resolve().parent
b64=''.join((HERE/f'raw.part{i:02d}.b64').read_text().strip() for i in range(12))
xz=base64.b64decode(b64)
assert hashlib.sha256(xz).hexdigest()=='6cb47870313e68c2a26c1f738528e98d3e8a8dece29390fa740237c8b3458132'
raw=lzma.decompress(xz)
assert hashlib.sha256(raw).hexdigest()=='9a4876108b3a6f25254b8fd033f0fa517ff16095b31840d518154128561a5a19'
(HERE/'raw.decoded.json').write_bytes(raw)
print(len(raw),hashlib.sha256(raw).hexdigest())
