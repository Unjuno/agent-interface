from __future__ import annotations
import argparse,base64,gzip,hashlib,io,tarfile
from pathlib import Path
EXPECTED=['model.py','cases.py','test_model.py','run_shard.py','aggregate.py','audit_a3.py','test_packaging.py','PLAN.md','SHARD_PLAN.json','FREEZE.json']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('bundle');ap.add_argument('out');a=ap.parse_args();raw=base64.b64decode(Path(a.bundle).read_text().strip(),validate=True);tar_bytes=gzip.decompress(raw);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(tar_bytes),mode='r:') as tf:
  names=tf.getnames()
  if names!=EXPECTED: raise SystemExit(f'bad members {names}')
  for m in tf.getmembers():
   if not m.isfile() or '/' in m.name or '..' in m.name: raise SystemExit('unsafe member')
   data=tf.extractfile(m).read();(out/m.name).write_bytes(data);print(m.name,hashlib.sha256(data).hexdigest())
if __name__=='__main__':main()
