import base64,hashlib,json,zlib
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'SHA256SUMS.json').read_text())
errors=[]
for name,digest in manifest.items():
    p=root/name
    if not p.exists(): errors.append('missing:'+name); continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=digest: errors.append('hash:'+name)
freeze=json.loads((root/'FREEZE.json').read_text())
corpus=zlib.decompress(base64.b64decode((root/'CORPUS.json.zlib.b64').read_text()))
if hashlib.sha256(corpus).hexdigest()!=freeze['sha256']['corpus.json']: errors.append('corpus_restore')
formal=zlib.decompress(base64.b64decode((root/'FORMAL_RESULT.json.zlib.b64').read_text()))
audit=json.loads((root/'formal/AUDIT.json').read_text())
if hashlib.sha256(formal).hexdigest()!=audit['formal_sha256']: errors.append('formal_restore')
print(json.dumps({'errors':errors,'checks':len(manifest)+2},sort_keys=True,indent=2))
raise SystemExit(bool(errors))
