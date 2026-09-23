import base64,gzip,hashlib,io,json,tarfile
from pathlib import Path
m=json.loads(Path("SOURCE_MANIFEST.json").read_text());s=Path("SOURCE_BUNDLE.b64").read_text();assert len(s)==m["base64_bytes"] and hashlib.sha256(s.encode()).hexdigest()==m["base64_sha256"];gz=base64.b64decode(s);assert hashlib.sha256(gz).hexdigest()==m["gzip_sha256"];tar=gzip.decompress(gz);assert hashlib.sha256(tar).hexdigest()==m["tar_sha256"]
with tarfile.open(fileobj=io.BytesIO(tar),mode="r:") as tf:
 for x in tf.getmembers():
  d=tf.extractfile(x).read();e=m["files"][x.name];assert len(d)==e["bytes"] and hashlib.sha256(d).hexdigest()==e["sha256"];p=Path("restored")/x.name;p.parent.mkdir(exist_ok=True);p.write_bytes(d)
print("source_bundle_ok")
