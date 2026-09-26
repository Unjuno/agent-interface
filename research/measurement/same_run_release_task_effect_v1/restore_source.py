import base64,hashlib,tarfile,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
raw=base64.b64decode((HERE/'SOURCE.tar.xz.b64').read_text().strip(),validate=True)
want='908753027945f5a8bfd265dcb59c54695c257ed4def292beca1b915e90587069'
if hashlib.sha256(raw).hexdigest()!=want: raise SystemExit('source capsule hash mismatch')
out=Path(sys.argv[1]); out.mkdir(parents=True,exist_ok=False)
arc=out/'SOURCE.tar.xz'; arc.write_bytes(raw)
with tarfile.open(arc,'r:xz') as tf: tf.extractall(out,filter='data')
print(want)
