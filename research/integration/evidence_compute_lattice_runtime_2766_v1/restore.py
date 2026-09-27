import base64, hashlib, json, lzma, tarfile, io, sys
from pathlib import Path
base=Path(__file__).resolve().parent; out=Path(sys.argv[1])
if out.exists(): raise SystemExit("destination exists")
cap=json.loads((base/"CAPSULE.json").read_text()); chunks=[]
for p in cap["parts"]:
 b=(base/p["name"]).read_bytes(); assert len(b)==p["bytes"] and hashlib.sha256(b).hexdigest()==p["sha256"]; chunks.append(b)
raw=base64.b64decode(b"".join(chunks)); assert len(raw)==cap["xz_bytes"] and hashlib.sha256(raw).hexdigest()==cap["xz_sha256"]
tar=lzma.decompress(raw); assert hashlib.sha256(tar).hexdigest()==cap["tar_sha256"]
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(tar),mode="r:") as tf:
 for m in tf.getmembers():
  p=Path(m.name)
  if p.is_absolute() or ".." in p.parts or not m.isfile(): raise SystemExit("unsafe member")
  data=tf.extractfile(m).read(); dst=out/p; dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(data)
lines=(out/"SHA256SUMS").read_text().splitlines(); assert len(lines)==cap["data_members"]
for line in lines:
 h,rel=line.split("  ",1); p=out/rel; assert hashlib.sha256(p.read_bytes()).hexdigest()==h
print(json.dumps({"restored":cap["members"],"status":"PASS"},sort_keys=True))
