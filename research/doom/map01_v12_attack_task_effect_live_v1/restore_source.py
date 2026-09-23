from pathlib import Path
import base64,hashlib,lzma,tarfile,io,json
here=Path(__file__).resolve().parent
raw=base64.b64decode((here/'SOURCE.tar.xz.b64').read_text())
expected='6ea0c791ac8b7a1b03e91cd4261654b5de43081cd3137ba636e0bd2214d0491a'
assert hashlib.sha256(raw).hexdigest()==expected
out=here/'restored-source';out.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:xz') as tf:tf.extractall(out,filter='data')
print(json.dumps({'sha256':expected,'members':sorted(p.name for p in out.iterdir())}))
