from pathlib import Path
import hashlib, zipfile
ROOT=Path(__file__).resolve().parent/"inputs"/"pr-7926"
archive=ROOT/"source-snapshots.zip"
errors=[]
n=0
with zipfile.ZipFile(archive) as z:
    names=set(z.namelist())
    for line in (ROOT/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        expected,rel=line.split(None,1); rel=rel.strip(); n+=1
        if rel.startswith("sources/"):
            member=rel
            data=z.read(member) if member in names else None
        else:
            p=ROOT/rel
            data=p.read_bytes() if p.exists() else None
        actual=hashlib.sha256(data).hexdigest() if data is not None else "MISSING"
        if actual!=expected: errors.append({"path":rel,"expected":expected,"actual":actual})
print({"entries":n,"errors":errors})
if errors: raise SystemExit(1)
