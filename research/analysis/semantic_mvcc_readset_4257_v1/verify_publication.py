import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
m=json.loads((root/'SHA256SUMS.json').read_text()); errors=[]
for n,d in m.items():
 p=root/n
 if not p.exists(): errors.append('missing:'+n); continue
 if hashlib.sha256(p.read_bytes()).hexdigest()!=d: errors.append('hash:'+n)
a=json.loads((root/'formal/AUDIT.json').read_text())
if a['decision']!='PASS_SEMANTIC_MVCC_READSET_SCOPED' or a['errors']!=[]: errors.append('audit')
c=json.loads((root/'formal/CONTROLS.json').read_text())
if len(c)!=12 or not all(c.values()): errors.append('controls')
print(json.dumps({'checks':len(m)+2,'errors':errors},sort_keys=True,indent=2)); raise SystemExit(bool(errors))
