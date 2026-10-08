from pathlib import Path
import base64,hashlib,json,sys,zipfile
r=Path(__file__).resolve().parent
m=json.loads((r/"EVIDENCE_MANIFEST.json").read_text())
out=Path(sys.argv[1] if len(sys.argv)>1 else "/tmp/temporal-stream-s1-evidence")
if out.exists(): raise SystemExit("destination exists")
chunks=[]
for p in m["parts"]:
 b=(r/p["name"]).read_bytes()
 if hashlib.sha256(b).hexdigest()!=p["sha256"]: raise SystemExit(p["name"]+": sha")
 chunks.append(b.decode().strip())
raw=base64.b64decode("".join(chunks),validate=True)
if len(raw)!=m["archive_bytes"] or hashlib.sha256(raw).hexdigest()!=m["archive_sha256"]: raise SystemExit("archive identity")
out.mkdir(parents=True)
zp=out/m["archive_name"]; zp.write_bytes(raw)
with zipfile.ZipFile(zp) as z:
 for info in z.infolist():
  q=Path(info.filename)
  if q.is_absolute() or ".." in q.parts: raise SystemExit("unsafe path")
 z.extractall(out/"expanded")
print("PASS_RESTORE", hashlib.sha256(raw).hexdigest(), len(z.namelist()))
