import base64,hashlib,json,zlib
from pathlib import Path
root=Path(__file__).resolve().parent
m=json.loads((root/"SHA256SUMS.json").read_text()); errors=[]
for n,d in m.items():
 p=root/n
 if not p.exists(): errors.append("missing:"+n)
 elif hashlib.sha256(p.read_bytes()).hexdigest()!=d: errors.append("hash:"+n)
raw=zlib.decompress(base64.b64decode((root/"FORMAL_RESULT.json.zlib.b64").read_text()))
if hashlib.sha256(raw).hexdigest()!=json.loads((root/"RESULT.json").read_text())["formal_sha256"]: errors.append("formal_restore")
print(json.dumps({"errors":errors,"checks":len(m)+1},sort_keys=True,indent=2))
raise SystemExit(bool(errors))
