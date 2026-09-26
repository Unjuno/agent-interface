from __future__ import annotations
import base64, hashlib, io, json, sys, tarfile
from pathlib import Path
INFO="EVIDENCE_INFO.json"
def main(dest):
    root=Path(__file__).resolve().parent; dest=Path(dest)
    if dest.exists(): raise SystemExit("destination exists")
    info=json.loads((root/INFO).read_text()); chunks=[]
    for part in info["parts"]:
        p=root/part["path"]; b=p.read_bytes()
        if hashlib.sha256(b).hexdigest()!=part["sha256"]: raise SystemExit("part hash mismatch")
        chunks.append(p.read_text().strip())
    data=base64.b64decode("".join(chunks),validate=True)
    if len(data)!=info["archive_bytes"] or hashlib.sha256(data).hexdigest()!=info["archive_sha256"]: raise SystemExit("archive identity mismatch")
    dest.mkdir(parents=True); total=0; count=0
    with tarfile.open(fileobj=io.BytesIO(data),mode="r:xz") as tf:
        for m in tf.getmembers():
            p=Path(m.name)
            if not m.isfile() or not m.name.startswith("formal/") or p.is_absolute() or ".." in p.parts: raise SystemExit("unsafe member")
            count+=1; total+=m.size
        if count!=info["member_count"] or total!=info["member_bytes"]: raise SystemExit("member envelope mismatch")
        tf.extractall(dest,filter="data")
    audit=(dest/"formal"/"AUDIT.json").read_bytes(); receipts=(dest/"formal"/"RECEIPTS.json").read_bytes()
    if hashlib.sha256(audit).hexdigest()!=info["formal_audit_sha256"]: raise SystemExit("audit hash mismatch")
    if hashlib.sha256(receipts).hexdigest()!=info["formal_receipts_sha256"]: raise SystemExit("receipts hash mismatch")
    print(json.dumps({"members":count,"bytes":total,"status":"PASS"},sort_keys=True))
if __name__=="__main__": main(sys.argv[1])
