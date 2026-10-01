import base64,hashlib,json,zlib
from pathlib import Path
root=Path(__file__).resolve().parent
m=json.loads((root/'SHA256SUMS.json').read_text())
errors=[]
for n,d in m.items():
 p=root/n
 if not p.exists(): errors.append('missing:'+n); continue
 if hashlib.sha256(p.read_bytes()).hexdigest()!=d: errors.append('hash:'+n)
raw=zlib.decompress(base64.b64decode((root/'FORMAL_RESULT.json.zlib.b64').read_text()))
a=json.loads((root/'formal/AUDIT.json').read_text())
if hashlib.sha256(raw).hexdigest()!=a['formal_sha256']: errors.append('formal_restore')
if a['decision']!='PASS_SEMANTIC_PREDICATE_FABRIC_SCOPED' or a['errors']!=[]: errors.append('audit')
c=json.loads((root/'formal/CONTROLS.json').read_text())
if len(c)!=12 or not all(c.values()): errors.append('controls')
print(json.dumps({'errors':errors,'checks':len(m)+3},sort_keys=True,indent=2))
raise SystemExit(bool(errors))
