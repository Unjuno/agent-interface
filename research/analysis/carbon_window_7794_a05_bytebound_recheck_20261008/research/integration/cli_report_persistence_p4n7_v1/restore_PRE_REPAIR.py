#!/usr/bin/env python3
from pathlib import Path
import base64,hashlib,json
root=Path(__file__).resolve().parent
meta=json.loads((root/'CAPSULE.json').read_text())
out=root/meta['source_filename']; h=hashlib.sha256()
with out.open('wb') as dst:
    for part in meta['parts']:
        txt=(root/'capsule'/part['name']).read_bytes()
        if hashlib.sha256(txt).hexdigest()!=part['text_sha256']: raise SystemExit('text part mismatch '+part['name'])
        data=base64.b64decode(txt)
        if len(data)!=part['decoded_size'] or hashlib.sha256(data).hexdigest()!=part['decoded_sha256']: raise SystemExit('decoded part mismatch '+part['name'])
        dst.write(data); h.update(data)
if out.stat().st_size!=meta['source_size'] or h.hexdigest()!=meta['source_sha256']: raise SystemExit('capsule mismatch')
print(json.dumps({'output':out.name,'size':out.stat().st_size,'sha256':h.hexdigest()},sort_keys=True))
