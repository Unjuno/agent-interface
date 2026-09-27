import base64,hashlib,json,tarfile,sys
from pathlib import Path
root=Path(__file__).resolve().parent; out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False); m=json.loads((root/'EVIDENCE_MANIFEST.json').read_text()); raw=b''
for p in m['parts']:
 b=base64.b64decode((root/p['name']).read_text()); assert len(b)==p['raw_bytes'] and hashlib.sha256(b).hexdigest()==p['raw_sha256']; raw+=b
assert len(raw)==m['archive_bytes'] and hashlib.sha256(raw).hexdigest()==m['archive_sha256']; tmp=out.parent/(out.name+'.tar.xz'); tmp.write_bytes(raw)
with tarfile.open(tmp,'r:xz') as tf: tf.extractall(out,filter='data')
tmp.unlink(); print(m['archive_sha256'])
