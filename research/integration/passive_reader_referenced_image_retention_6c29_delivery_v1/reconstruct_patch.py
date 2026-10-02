#!/usr/bin/env python3
import hashlib, json, pathlib, sys
base=pathlib.Path(__file__).resolve().parent
manifest=json.loads((base/'PATCH_MANIFEST.json').read_text())
out=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path('/tmp/image-retention-6c29.patch')
if out.exists(): raise SystemExit('refuse existing output')
chunks=[]
for p in manifest['parts']:
    b=(base/p['path']).read_bytes()
    if len(b)!=p['bytes'] or hashlib.sha256(b).hexdigest()!=p['sha256']: raise SystemExit('part mismatch: '+p['path'])
    chunks.append(b)
blob=b''.join(chunks); exp=manifest['patch']
if len(blob)!=exp['bytes'] or hashlib.sha256(blob).hexdigest()!=exp['sha256']: raise SystemExit('patch mismatch')
out.write_bytes(blob)
print(json.dumps({'status':'PASS_RECONSTRUCT','bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'output':str(out)},sort_keys=True))
