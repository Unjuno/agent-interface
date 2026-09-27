import base64,hashlib,json,zlib
from pathlib import Path
root=Path(__file__).resolve().parent
m=json.loads((root/"SHA256SUMS.json").read_text()); errors=[]
for n,d in m.items():
 p=root/n
 if not p.exists(): errors.append("missing:"+n); continue
 if hashlib.sha256(p.read_bytes()).hexdigest()!=d: errors.append("hash:"+n)
a=json.loads((root/"formal/AUDIT.json").read_text())
if a["decision"]!="PASS_VERSIONED_PREDICATE_SPECIALIST_SWITCH_SCOPED" or a["errors"]!=[]: errors.append("audit")
c=json.loads((root/"formal/CONTROLS.json").read_text())
if sum(bool(v) for v in c.values())<10: errors.append("controls_gate")
p=json.loads((root/"formal/POSTHOC_CONTROLS.json").read_text())
if not all(p.values()): errors.append("posthoc_controls")
raw=zlib.decompress(base64.b64decode((root/"FORMAL_RESULT.json.zlib.b64").read_text()))
if hashlib.sha256(raw).hexdigest()!=a["formal_sha256"]: errors.append("formal_restore")
print(json.dumps({"checks":len(m)+4,"errors":errors},sort_keys=True,indent=2)); raise SystemExit(bool(errors))
