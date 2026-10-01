#!/usr/bin/env python3
import base64,hashlib,json,tarfile,sys
from pathlib import Path
here=Path(__file__).resolve().parent
m=json.loads((here/'EVIDENCE_MANIFEST.json').read_text())
out=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/issue4144-evidence').resolve()
if out.exists(): raise SystemExit(f'refuse existing destination: {out}')
enc=bytearray()
for p in m['parts']:
    raw=(here/'evidence'/p['name']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=p['sha256']: raise SystemExit('part hash mismatch:'+p['name'])
    enc.extend(raw.strip())
arc=base64.b64decode(bytes(enc),validate=True)
if len(arc)!=m['archive']['bytes'] or hashlib.sha256(arc).hexdigest()!=m['archive']['sha256']: raise SystemExit('archive identity mismatch')
out.mkdir(parents=True); ap=out/'EVIDENCE.tar.xz'; ap.write_bytes(arc)
with tarfile.open(ap,'r:xz') as tf:
    root=out.resolve()
    for x in tf.getmembers():
        dest=(out/x.name).resolve()
        if root not in dest.parents and dest!=root: raise SystemExit('unsafe member:'+x.name)
        if x.issym() or x.islnk(): raise SystemExit('links forbidden:'+x.name)
    tf.extractall(out,filter='data')
print(out)
