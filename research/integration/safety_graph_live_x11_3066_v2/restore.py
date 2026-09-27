from __future__ import annotations
import argparse,base64,hashlib,lzma,tarfile,io
from pathlib import Path
ARCHIVE_SHA='1f854960137ea7b7e17e49a108864776f47041d2e50de4e89bda19e7c35b2164'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('part');ap.add_argument('out');a=ap.parse_args()
 out=Path(a.out)
 if out.exists():raise SystemExit('destination exists')
 b64=Path(a.part).read_text().strip();data=base64.b64decode(b64,validate=True)
 if hashlib.sha256(data).hexdigest()!=ARCHIVE_SHA:raise SystemExit('archive hash mismatch')
 raw=lzma.decompress(data);out.mkdir(parents=True)
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
  members=tf.getmembers()
  for m in members:
   p=Path(m.name)
   if p.is_absolute() or '..' in p.parts or not (m.isfile() or m.isdir()):raise SystemExit('unsafe member')
  tf.extractall(out,filter='data')
 print('RESTORED',len(members))
if __name__=='__main__':main()
