import base64,hashlib,json,lzma,tarfile,io,sys
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/"SHA256SUMS.json").read_text()); errors=[]
for n,d in manifest.items():
 p=root/n
 if not p.exists(): errors.append("missing:"+n); continue
 if hashlib.sha256(p.read_bytes()).hexdigest()!=d: errors.append("hash:"+n)
meta=json.loads((root/"CAPSULE.json").read_text())
xz=base64.b64decode((root/"FORMAL_EVIDENCE.tar.xz.b64").read_text())
if hashlib.sha256(xz).hexdigest()!=meta["decoded_xz_sha256"]: errors.append("capsule_hash")
else:
 tar=lzma.decompress(xz)
 if hashlib.sha256(tar).hexdigest()!=meta["tar_sha256"]: errors.append("tar_hash")
 else:
  with tarfile.open(fileobj=io.BytesIO(tar),mode="r:") as tf:
   names=tf.getnames()
   if set(names)!=set(meta["members"]): errors.append("member_set")
   for m in tf.getmembers():
    if not m.isfile() or Path(m.name).name!=m.name: errors.append("unsafe_member:"+m.name); continue
    data=tf.extractfile(m).read(); e=meta["members"].get(m.name,{})
    if len(data)!=e.get("size") or hashlib.sha256(data).hexdigest()!=e.get("sha256"): errors.append("member:"+m.name)
print(json.dumps({"errors":errors,"checks":len(manifest)+2+meta["member_count"]},sort_keys=True,indent=2))
raise SystemExit(bool(errors))
