import base64,gzip,hashlib,io,json,tarfile
from pathlib import Path
m=json.loads(Path("SOURCE_MANIFEST.json").read_text())
text="".join(Path(p["name"]).read_text() for p in m["bundle"]["parts"])
assert hashlib.sha256(text.encode()).hexdigest()==m["bundle"]["b64_sha256"]
gz=base64.b64decode(text)
assert hashlib.sha256(gz).hexdigest()==m["bundle"]["gzip_sha256"]
tar=gzip.decompress(gz)
assert hashlib.sha256(tar).hexdigest()==m["bundle"]["tar_sha256"]
with tarfile.open(fileobj=io.BytesIO(tar),mode="r:") as tf:
    for member in tf.getmembers():
        b=tf.extractfile(member).read(); exp=m["files"][member.name]
        assert len(b)==exp["bytes"] and hashlib.sha256(b).hexdigest()==exp["sha256"]
        out=Path("restored")/member.name; out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(b)
print("source_bundle_ok")
