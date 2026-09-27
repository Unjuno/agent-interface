import base64,gzip,hashlib,io,json,tarfile
from pathlib import Path
m=json.loads(Path("SOURCE_MANIFEST.json").read_text()); text=Path("SOURCE_BUNDLE.b64").read_text(); assert hashlib.sha256(text.encode()).hexdigest()==m["bundle"]["b64_sha256"]; gz=base64.b64decode(text); assert hashlib.sha256(gz).hexdigest()==m["bundle"]["gzip_sha256"]; tar=gzip.decompress(gz); assert hashlib.sha256(tar).hexdigest()==m["bundle"]["tar_sha256"]
with tarfile.open(fileobj=io.BytesIO(tar),mode="r:") as tf:
 for x in tf.getmembers():
  b=tf.extractfile(x).read(); e=m["files"][x.name]; assert len(b)==e["bytes"] and hashlib.sha256(b).hexdigest()==e["sha256"]; p=Path("restored")/x.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
print("source_bundle_ok")
