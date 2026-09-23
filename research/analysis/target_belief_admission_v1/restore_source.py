from pathlib import Path
import base64, hashlib, io, lzma, tarfile
p=Path(__file__).resolve().parent
txt=(p/'SOURCE.tar.xz.b64').read_text().strip()
assert hashlib.sha256(txt.encode()).hexdigest()=='4a85f5189bc898d4d77e9087cd9ce3ffb9903406e105ae1e63dea0821d6e40ed'
xz=base64.b64decode(txt,validate=True)
assert hashlib.sha256(xz).hexdigest()=='0aa33991d4a47747e060fde90b0e17cca3b5b9ac02338e2d048e72428c4dcfae'
out=p/'restored_source'
out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(xz),mode='r:xz') as tf:
    tf.extractall(out,filter='data')
print(out)
