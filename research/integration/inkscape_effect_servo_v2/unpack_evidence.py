#!/usr/bin/env python3
import base64,hashlib,json,tarfile,lzma,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
 m=json.loads((ROOT/'EVIDENCE_MANIFEST.json').read_text()); data=b''
 for x in m['parts']:
  p=ROOT/'evidence'/x['file']; b=p.read_bytes(); assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']; data+=base64.b64decode(b)
 assert len(data)==m['archive_bytes'] and hashlib.sha256(data).hexdigest()==m['archive_sha256']
 out=Path(sys.argv[1]).resolve(); assert not out.exists(); out.mkdir(parents=True)
 tmp=out/'evidence.tar.xz'; tmp.write_bytes(data)
 with tarfile.open(tmp,'r:xz') as tf:
  for x in tf.getmembers():
   assert x.isfile() and not x.name.startswith('/') and '..' not in Path(x.name).parts
  tf.extractall(out/'files',filter='data')
 mani=json.loads((out/'files'/'MANIFEST.json').read_text())
 for x in mani['members']:
  p=out/'files'/x['path']; assert p.is_file() and p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
 print(json.dumps({'archive_sha256':m['archive_sha256'],'members':len(mani['members']),'ok':True},sort_keys=True))
if __name__=='__main__': main()
