import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'SHA256SUMS.json').read_text())
errors=[]
for name,digest in manifest.items():
 p=root/name
 if not p.exists(): errors.append('missing:'+name); continue
 if hashlib.sha256(p.read_bytes()).hexdigest()!=digest: errors.append('hash:'+name)
a=json.loads((root/'formal/AUDIT.json').read_text())
if a['decision']!='PASS_DEPENDENCY_SCOPED_PREDICATE_CACHE_SCOPED' or a['errors']!=[]: errors.append('audit')
c=json.loads((root/'formal/CONTROLS.json').read_text())
if len(c)!=12 or not all(c.values()): errors.append('controls')
print(json.dumps({'errors':errors,'checks':len(manifest)+2},sort_keys=True,indent=2))
raise SystemExit(bool(errors))
