from pathlib import Path
import base64, hashlib, io, lzma, tarfile
HERE=Path(__file__).resolve().parent
b=base64.b64decode((HERE/"SOURCE.tar.xz.b64").read_text().strip())
assert hashlib.sha256(b).hexdigest()=="daad816cef866df63424dc7351ec1cf84de5a9983f0c9326fe032d760736b874"
out=HERE/"restored_source"
out.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(b),mode="r:xz") as tf: tf.extractall(out)
print(out)
