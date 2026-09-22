from __future__ import annotations
import hashlib, json, lzma, sys, tarfile
from pathlib import Path, PurePosixPath
ROOT=Path(__file__).resolve().parent
def die(msg): raise SystemExit(msg)
if len(sys.argv)!=2: die("usage: unpack_evidence.py NEW_DEST")
dest=Path(sys.argv[1])
if dest.exists(): die("destination already exists")
m=json.loads((ROOT/"PUBLICATION_MANIFEST.json").read_text())
chunks=[]
for row in m["archive"]["parts"]:
    b=(ROOT/row["name"]).read_bytes()
    if len(b)!=row["bytes"] or hashlib.sha256(b).hexdigest()!=row["sha256"]: die("part mismatch: "+row["name"])
    chunks.append(b)
data=b"".join(chunks)
if len(data)!=m["archive"]["bytes"] or hashlib.sha256(data).hexdigest()!=m["archive"]["sha256"]: die("archive mismatch")
raw=lzma.decompress(data)
dest.mkdir()
with tarfile.open(fileobj=__import__("io").BytesIO(raw),mode="r:") as t:
    members=t.getmembers()
    if len(members)!=m["archive"]["members_total"] or sum(x.isfile() for x in members)!=m["archive"]["file_members"]: die("member count mismatch")
    seen=set()
    for x in members:
        p=PurePosixPath(x.name)
        if p.is_absolute() or ".." in p.parts or x.name in seen or not (x.isfile() or x.isdir()): die("unsafe archive member")
        seen.add(x.name)
    t.extractall(dest,filter="data")
print(json.dumps({"status":"PASS_BYTE_RETENTION_ONLY","members_total":len(members),"file_members":sum(x.isfile() for x in members),"destination":str(dest)},sort_keys=True))
