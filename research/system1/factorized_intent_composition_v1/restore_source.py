from pathlib import Path
import base64, hashlib, lzma, tarfile, io
HERE=Path(__file__).resolve().parent
data=base64.b64decode((HERE/"SOURCE.tar.xz.b64").read_text().strip())
assert hashlib.sha256(data).hexdigest()=="a7add55ad88b9a3f90a798e6128f82b42ec48f0c53b3792fb45a961877a844d4"
out=HERE/"restored_source"
out.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(data),mode="r:xz") as tf:
    tf.extractall(out)
print(out)
