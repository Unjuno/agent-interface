import base64,hashlib,json,lzma,tarfile,io,sys
from pathlib import Path
root=Path(__file__).resolve().parent
if len(sys.argv)!=2: raise SystemExit("usage: unpack_evidence.py NEW_DIRECTORY")
out=Path(sys.argv[1])
if out.exists(): raise SystemExit("destination exists")
meta=json.loads((root/"CAPSULE.json").read_text())
xz=base64.b64decode((root/"FORMAL_EVIDENCE.tar.xz.b64").read_text())
assert len(xz)==meta["decoded_xz_size"] and hashlib.sha256(xz).hexdigest()==meta["decoded_xz_sha256"]
tar=lzma.decompress(xz)
assert len(tar)==meta["tar_size"] and hashlib.sha256(tar).hexdigest()==meta["tar_sha256"]
out.mkdir()
with tarfile.open(fileobj=io.BytesIO(tar),mode="r:") as tf:
    names=tf.getnames(); assert len(names)==meta["member_count"] and set(names)==set(meta["members"])
    for m in tf.getmembers():
        if not m.isfile() or Path(m.name).name!=m.name: raise SystemExit("unsafe member")
        data=tf.extractfile(m).read(); e=meta["members"][m.name]
        assert len(data)==e["size"] and hashlib.sha256(data).hexdigest()==e["sha256"]
        (out/m.name).write_bytes(data)
print(json.dumps({"members":len(names),"capsule_sha256":meta["decoded_xz_sha256"]},sort_keys=True))
