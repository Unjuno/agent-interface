from pathlib import Path
import base64,hashlib,tarfile,io,sys
root=Path(__file__).resolve().parent
out=Path(sys.argv[1])
if out.exists(): raise SystemExit('destination exists')
parts=sorted(root.glob('capsule.*'))
raw=base64.b64decode(''.join(p.read_text() for p in parts))
if hashlib.sha256(raw).hexdigest()!='87b25441e4acf06d6ba8204b4d4c837b94cc9b1cb8c6e6b54a4ef6b761e6468a': raise SystemExit('capsule sha mismatch')
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:xz') as tf:
 for m in tf.getmembers():
  if not m.isfile() or '/' in m.name or m.name.startswith('.'): raise SystemExit('unsafe member')
  data=tf.extractfile(m).read(); (out/m.name).write_bytes(data)
print('restored',len(list(out.iterdir())))
