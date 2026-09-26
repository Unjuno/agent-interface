from __future__ import annotations
import argparse,base64,hashlib,json,tarfile
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent

def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('out'); a=ap.parse_args(); out=Path(a.out)
 if out.exists(): raise SystemExit('refuse_existing_destination')
 m=json.loads((HERE/'EVIDENCE_MANIFEST.json').read_text()); chunks=[]
 for p in m['parts']:
  b=base64.b64decode((HERE/p['path']).read_text())
  if len(b)!=p['binary_bytes'] or sha(b)!=p['binary_sha256']: raise SystemExit(f"part_mismatch:{p['path']}")
  chunks.append(b)
 ar=b''.join(chunks)
 if len(ar)!=m['archive_bytes'] or sha(ar)!=m['archive_sha256']: raise SystemExit('archive_mismatch')
 tmp=HERE/'.evidence.verify.tmp.tar.xz'; tmp.write_bytes(ar)
 try:
  with tarfile.open(tmp,'r:xz') as tf:
   ms=[x for x in tf.getmembers() if x.isfile()]
   names=[x.name for x in ms]
   if len(ms)!=m['member_count'] or len(names)!=len(set(names)): raise SystemExit('member_count_or_duplicate')
   for n in names:
    pp=PurePosixPath(n)
    if pp.is_absolute() or '..' in pp.parts: raise SystemExit('unsafe_path')
   out.mkdir(parents=True); tf.extractall(out,filter='data')
 finally:
  if tmp.exists(): tmp.unlink()
 lines=(out/m['checksum_member']).read_text().splitlines(); seen=set()
 for line in lines:
  digest,path=line.split('  ',1); p=out/path
  if path in seen or not p.is_file() or sha(p.read_bytes())!=digest: raise SystemExit(f'checksum:{path}')
  seen.add(path)
 if len(seen)!=m['member_count']-1: raise SystemExit('checksum_denominator')
 print(json.dumps({'status':'PASS_BYTE_RETENTION_ONLY','archive_sha256':m['archive_sha256'],'members':m['member_count']},sort_keys=True))
if __name__=='__main__': main()
