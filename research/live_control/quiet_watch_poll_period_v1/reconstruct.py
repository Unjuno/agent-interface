#!/usr/bin/env python3
import hashlib, json, lzma, sys
from pathlib import Path
here=Path(__file__).resolve().parent
out=Path(sys.argv[1]) if len(sys.argv)>1 else here/'measured.reconstructed.json'
manifest=json.loads((here/'evidence_manifest.json').read_text())
chunks=[]
for item in manifest['parts']:
    b=(here/item['path']).read_bytes()
    if hashlib.sha256(b).hexdigest()!=item['sha256']:
        raise SystemExit(f"part hash mismatch: {item['path']}")
    chunks.append(b)
xz=b''.join(chunks)
if hashlib.sha256(xz).hexdigest()!=manifest['measured_xz_sha256']:
    raise SystemExit('archive hash mismatch')
raw=lzma.decompress(xz)
h=hashlib.sha256(raw).hexdigest()
if h != manifest['measured_json_sha256']:
    raise SystemExit(f'measured hash mismatch {h}')
out.write_bytes(raw)
print(h, out)
