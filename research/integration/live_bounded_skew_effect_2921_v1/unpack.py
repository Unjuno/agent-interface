#!/usr/bin/env python3
import base64,hashlib,io,lzma,pathlib,tarfile
EXPECTED='cae9a44ab04e226687c0e0bb0b4fd6f9e71402ac6f08158b5875d36c06b4b5b1'
def main():
 import argparse; ap=argparse.ArgumentParser(); ap.add_argument('out'); a=ap.parse_args(); out=pathlib.Path(a.out)
 if out.exists(): raise SystemExit('destination exists')
 xz=base64.b64decode(pathlib.Path('EVIDENCE.tar.xz.b64').read_text().strip(),validate=True)
 if hashlib.sha256(xz).hexdigest()!=EXPECTED: raise SystemExit('archive hash mismatch')
 raw=lzma.decompress(xz); out.mkdir()
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
  for m in tf.getmembers():
   p=pathlib.PurePosixPath(m.name)
   if p.is_absolute() or '..' in p.parts or not m.isfile(): raise SystemExit('unsafe archive member')
  tf.extractall(out,filter='data')
 print(f'PASS files={len([p for p in out.rglob("*") if p.is_file()])} sha256={EXPECTED}')
if __name__=='__main__': main()
