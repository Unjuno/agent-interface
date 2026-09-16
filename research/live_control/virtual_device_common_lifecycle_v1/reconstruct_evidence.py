#!/usr/bin/env python3
from pathlib import Path
import base64,hashlib
ROOT=Path(__file__).resolve().parent
EXPECTED_BYTES=52151
EXPECTED_SHA256='c996533d4e566bd11c1c6a9b04ef2d19405104918c55d35386c59bbf6918beeb'
parts=sorted(ROOT.glob('evidence.part*.b64'))
raw=base64.b64decode(''.join(p.read_text().split() for p in parts),validate=True)
assert len(raw)==EXPECTED_BYTES,(len(raw),EXPECTED_BYTES)
assert hashlib.sha256(raw).hexdigest()==EXPECTED_SHA256
out=ROOT/'evidence.tar.gz';out.write_bytes(raw)
print({'ok':True,'parts':len(parts),'bytes':len(raw),'sha256':EXPECTED_SHA256})
