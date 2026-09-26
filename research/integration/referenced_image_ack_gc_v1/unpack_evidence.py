#!/usr/bin/env python3
import base64, hashlib, json, tarfile, sys
from pathlib import Path
here=Path(__file__).resolve().parent
m=json.loads((here/'EVIDENCE_MANIFEST.json').read_text())
out=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/referenced-image-ack-gc-review').resolve()
if out.exists():
    raise SystemExit(f'refuse existing destination: {out}')
encoded=bytearray()
for p in m['parts']:
    raw=(here/'evidence'/p['name']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=p['sha256']:
        raise SystemExit(f"part hash mismatch: {p['name']}")
    encoded.extend(raw.strip())
archive=base64.b64decode(bytes(encoded),validate=True)
if len(archive)!=m['archive']['decoded_bytes'] or hashlib.sha256(archive).hexdigest()!=m['archive']['sha256']:
    raise SystemExit('archive identity mismatch')
out.mkdir(parents=True)
arc=out/'EVIDENCE.tar.xz'; arc.write_bytes(archive)
with tarfile.open(arc,'r:xz') as tf:
    root=out.resolve()
    for member in tf.getmembers():
        target=(out/member.name).resolve()
        if root not in target.parents and target!=root:
            raise SystemExit(f'unsafe member: {member.name}')
        if member.issym() or member.islnk():
            raise SystemExit(f'links forbidden: {member.name}')
    tf.extractall(out,filter='data')
for name,(sha,size) in m['members'].items():
    raw=(out/name).read_bytes()
    if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:
        raise SystemExit(f'member mismatch: {name}')
print(out)
