import base64,hashlib,lzma,tarfile,io,json
from pathlib import Path
p=Path(__file__).resolve().parent
manifest=json.loads((p/"SOURCE_BUNDLE.json").read_text())
archive=base64.b64decode((p/"SOURCE_BUNDLE.b64").read_text())
assert hashlib.sha256(archive).hexdigest()==manifest["archive_sha256"]
with tarfile.open(fileobj=io.BytesIO(archive),mode="r:xz") as tf:
    tf.extractall("SOURCE_BUNDLE.restored")
print(manifest["archive_sha256"])
