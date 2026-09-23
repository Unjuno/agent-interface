import base64,hashlib,io,json,lzma,sys,tarfile
from pathlib import Path
here=Path(__file__).resolve().parent
out=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/versioned-predicate-specialist-switch-4284")
if out.exists(): raise SystemExit("refuse existing output")
m=json.loads((here/"EVIDENCE_MANIFEST.json").read_text())
chunks=[]
for x in m["parts"]:
    b=(here/x["file"]).read_bytes()
    if len(b)!=x["bytes"] or hashlib.sha256(b).hexdigest()!=x["sha256"]: raise SystemExit("part mismatch "+x["file"])
    chunks.append(b.strip())
xz=base64.b64decode(b"".join(chunks),validate=True)
if len(xz)!=m["decoded_xz_bytes"] or hashlib.sha256(xz).hexdigest()!=m["decoded_xz_sha256"]: raise SystemExit("archive identity mismatch")
raw=lzma.decompress(xz); out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode="r:") as t:
    members=t.getmembers()
    if len(members)!=m["members"]: raise SystemExit("member count mismatch")
    for x in members:
        if not x.isfile() or x.name.startswith("/") or ".." in Path(x.name).parts: raise SystemExit("unsafe member")
    t.extractall(out,filter="data")
for name,digest in m["source_sha256"].items():
    if hashlib.sha256((out/name).read_bytes()).hexdigest()!=digest: raise SystemExit("source hash mismatch "+name)
if hashlib.sha256((out/"formal-01/RAW.json").read_bytes()).hexdigest()!=m["formal_raw_sha256"]: raise SystemExit("raw hash mismatch")
print("PASS_EVIDENCE_RESTORE",len(members),m["decoded_xz_sha256"])
