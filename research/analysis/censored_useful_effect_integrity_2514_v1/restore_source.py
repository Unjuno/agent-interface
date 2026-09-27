from pathlib import Path
import argparse,base64,hashlib,lzma,tarfile,io
p=argparse.ArgumentParser();p.add_argument('b64');p.add_argument('dest');p.add_argument('--sha256',required=True);a=p.parse_args()
raw=base64.b64decode(Path(a.b64).read_text())
if hashlib.sha256(raw).hexdigest()!=a.sha256: raise SystemExit('capsule sha256 mismatch')
d=Path(a.dest);d.mkdir(parents=True,exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(lzma.decompress(raw)),mode='r:') as tf:
    for m in tf.getmembers():
        if not m.isfile() or '/' in m.name or m.name.startswith('.'): raise SystemExit('unsafe member')
    tf.extractall(d)
print('restored',len(list(d.iterdir())))
