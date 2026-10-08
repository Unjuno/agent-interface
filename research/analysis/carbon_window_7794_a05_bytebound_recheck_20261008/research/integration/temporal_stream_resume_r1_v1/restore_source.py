from pathlib import Path
import base64,hashlib,json,lzma,tarfile,io,sys
r=Path(__file__).resolve().parent;m=json.loads((r/"SOURCE_PARTS.json").read_text()); chunks=[]
for p in m["parts"]:
 b=(r/p["name"]).read_bytes();
 if len(b)!=p["bytes"] or hashlib.sha256(b).hexdigest()!=p["sha256"]: raise SystemExit(p["name"]+": identity")
 chunks.append(b.decode().strip())
s="".join(chunks);raw=base64.b64decode(s,validate=True)
if hashlib.sha256(raw).hexdigest()!=m["xz_sha256"]: raise SystemExit("xz identity")
out=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/temporal-resume-source")
if out.exists(): raise SystemExit("destination exists")
out.mkdir(parents=True)
data=lzma.decompress(raw)
with tarfile.open(fileobj=io.BytesIO(data),mode="r:") as t:
 for x in t.getmembers():
  q=Path(x.name)
  if q.is_absolute() or ".." in q.parts or not x.isfile(): raise SystemExit("unsafe member")
 t.extractall(out)
print("PASS_SOURCE_RESTORE",len(list(out.iterdir())))
