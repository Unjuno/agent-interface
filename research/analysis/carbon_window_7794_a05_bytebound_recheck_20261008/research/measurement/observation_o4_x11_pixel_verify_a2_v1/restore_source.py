from __future__ import annotations
import argparse,base64,gzip,hashlib,io,tarfile
from pathlib import Path
EXPECTED=['BATCH_PLAN.json','PACKAGING_CONSTRUCTION.json','PLAN.md','PLAN_A2.md','SCHEDULE.json','aggregate.py','audit.py','audit_a2.py','batch_runner.py','fixture.py','runner.py']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('bundle');ap.add_argument('out');a=ap.parse_args();raw=base64.b64decode(Path(a.bundle).read_text().strip(),validate=True);tar_bytes=gzip.decompress(raw);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(tar_bytes),mode='r:') as tf:
  names=sorted(tf.getnames());
  if names!=sorted(EXPECTED): raise SystemExit(f'bad members {names}')
  for m in tf.getmembers():
   if not m.isfile() or '/' in m.name or '..' in m.name: raise SystemExit('unsafe member')
   data=tf.extractfile(m).read();(out/m.name).write_bytes(data);print(m.name,hashlib.sha256(data).hexdigest())
if __name__=='__main__':main()
