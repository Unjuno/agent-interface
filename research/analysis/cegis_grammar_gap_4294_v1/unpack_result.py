import base64,hashlib,io,json,lzma,tarfile
from pathlib import Path
p=Path(__file__).resolve().parent
m=json.loads((p/"RESULT_BUNDLE.json").read_text())
s="".join((p/c["name"]).read_text().strip() for c in m["chunks"])
a=base64.b64decode(s)
assert hashlib.sha256(a).hexdigest()==m["archive_sha256"]
with tarfile.open(fileobj=io.BytesIO(a),mode="r:xz") as tf: tf.extractall("RESULT_BUNDLE.restored")
print(m["archive_sha256"])
