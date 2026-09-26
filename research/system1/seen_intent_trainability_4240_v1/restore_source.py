from pathlib import Path
import base64, hashlib, tarfile, io
HERE=Path(__file__).resolve().parent
data=base64.b64decode((HERE/"SOURCE.tar.xz.b64").read_text().strip())
assert hashlib.sha256(data).hexdigest()=="584cd892eb5c0458ab60970b0d18d62f86e7aaf779e20b03976d47fcd7f8feba"
out=HERE/"restored_source"
out.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(data),mode="r:xz") as tf:
    tf.extractall(out)
print(out)
