from __future__ import annotations
import argparse,base64,hashlib,lzma,tarfile,io
from pathlib import Path
XZ_SHA='42e156b647b3feecd5d7c0fefd165ff3f14bea3e675825c78e8539e2f5cb1fd3'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('capsule'); ap.add_argument('out'); a=ap.parse_args()
    out=Path(a.out)
    if out.exists(): raise SystemExit('destination exists')
    xz=base64.b64decode(Path(a.capsule).read_text().strip(),validate=True)
    if hashlib.sha256(xz).hexdigest()!=XZ_SHA: raise SystemExit('xz hash mismatch')
    tar=lzma.decompress(xz); out.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(tar),mode='r:') as tf:
        for m in tf.getmembers():
            p=Path(m.name)
            if p.is_absolute() or '..' in p.parts or not m.isfile(): raise SystemExit('unsafe member')
        tf.extractall(out,filter='data')
    print('RESTORED')
if __name__=='__main__': main()
