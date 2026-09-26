from __future__ import annotations
import argparse,base64,hashlib,lzma,tarfile,io
from pathlib import Path
XZ_SHA='12232a8ca94304565dfe289a772b9fa4e92498162fde5065264b9b11e8be2131'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('parts',nargs='+'); a=ap.parse_args()
    out=Path(a.out)
    if out.exists(): raise SystemExit('destination exists')
    text=''.join(Path(p).read_text().strip() for p in a.parts)
    xz=base64.b64decode(text,validate=True)
    if hashlib.sha256(xz).hexdigest()!=XZ_SHA: raise SystemExit('xz hash mismatch')
    tar=lzma.decompress(xz); out.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(tar),mode='r:') as tf:
        for m in tf.getmembers():
            p=Path(m.name)
            if p.is_absolute() or '..' in p.parts or not m.isfile(): raise SystemExit('unsafe member')
        tf.extractall(out,filter='data')
    print('RESTORED')
if __name__=='__main__': main()
