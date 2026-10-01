#!/usr/bin/env python3
import base64, hashlib, json, tarfile, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
PACK=json.loads((HERE/'PACK.json').read_text())
dst=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/tmp/key-up-telemetry-4130')
if dst.exists():
    raise SystemExit(f'destination exists: {dst}')
encoded=[]
for part in PACK['parts']:
    p=HERE/'evidence_parts'/part['name']
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=part['sha256']:
        raise SystemExit(f'part hash mismatch: {p.name}')
    encoded.append(raw.strip())
payload=base64.b64decode(b''.join(encoded), validate=True)
if len(payload)!=PACK['archive_bytes'] or hashlib.sha256(payload).hexdigest()!=PACK['archive_sha256']:
    raise SystemExit('archive identity mismatch')
archive=HERE/'evidence.restored.tar.xz'
archive.write_bytes(payload)
dst.mkdir()
with tarfile.open(archive,'r:xz') as tf:
    tf.extractall(dst, filter='data')
print(json.dumps({'archive_sha256':PACK['archive_sha256'],'destination':str(dst)},sort_keys=True))
