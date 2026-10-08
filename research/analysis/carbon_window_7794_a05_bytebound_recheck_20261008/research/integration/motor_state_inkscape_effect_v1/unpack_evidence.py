#!/usr/bin/env python3
import base64,hashlib,json,sys
from pathlib import Path
here=Path(__file__).resolve().parent
m=json.loads((here/'PACK.json').read_text())
s=b''
for p in m['parts']:
 b=(here/p['name']).read_bytes()
 if len(b)!=p['bytes'] or hashlib.sha256(b).hexdigest()!=p['sha256']: raise SystemExit('part mismatch: '+p['name'])
 s+=b
raw=base64.b64decode(s,validate=True)
if len(raw)!=m['decoded_bytes'] or hashlib.sha256(raw).hexdigest()!=m['decoded_sha256']: raise SystemExit('archive mismatch')
out=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/motor-state-inkscape-effect.tar.xz')
if out.exists(): raise SystemExit('refuse existing output')
out.write_bytes(raw); print(out, len(raw), m['decoded_sha256'])
