import base64,hashlib,json,tarfile,sys
from pathlib import Path
H=Path(__file__).resolve().parent
m=json.loads((H/'EVIDENCE_MANIFEST.json').read_text())
raw=base64.b64decode((H/'EVIDENCE.tar.xz.b64').read_text().strip(),validate=True)
if len(raw)!=m['archive_bytes'] or hashlib.sha256(raw).hexdigest()!=m['archive_sha256']: raise SystemExit('archive mismatch')
out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False)
arc=out/'EVIDENCE.tar.xz'; arc.write_bytes(raw)
with tarfile.open(arc,'r:xz') as tf: tf.extractall(out,filter='data')
print(m['archive_sha256'])
