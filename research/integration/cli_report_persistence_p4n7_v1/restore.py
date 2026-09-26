#!/usr/bin/env python3
from pathlib import Path
import base64,hashlib,json
root=Path(__file__).resolve().parent
meta=json.loads((root/'CAPSULE.json').read_text())
out=root/meta['source_filename']
h=hashlib.sha256()
with out.open('wb') as dst:
    for part in meta['parts']:
        text=(root/'capsule'/part['name']).read_bytes()
        if hashlib.sha256(text).hexdigest()!=part['text_sha256']:
            raise SystemExit(f"text part mismatch: {part['name']}")
        data=base64.b64decode(text,validate=False)
        if len(data)!=part['decoded_size'] or hashlib.sha256(data).hexdigest()!=part['decoded_sha256']:
            raise SystemExit(f"decoded part mismatch: {part['name']}")
        dst.write(data); h.update(data)
if out.stat().st_size!=meta['source_size'] or h.hexdigest()!=meta['source_sha256']:
    raise SystemExit('capsule mismatch')
print(json.dumps({'output':str(out),'size':out.stat().st_size,'sha256':h.hexdigest()},sort_keys=True))
