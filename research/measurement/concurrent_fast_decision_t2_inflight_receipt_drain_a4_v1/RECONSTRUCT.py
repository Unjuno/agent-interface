# Audit reconstruction only; not a new scientific allocation.
from pathlib import Path
import base64, hashlib, io, json, subprocess, sys, tarfile, tempfile
HERE=Path(__file__).resolve().parent
M=json.loads((HERE/'RETENTION_MANIFEST.json').read_text())

def join_decode(names):
    return base64.b64decode(''.join((HERE/n).read_text(encoding='ascii') for n in names))

with tempfile.TemporaryDirectory(prefix='ai1459-reconstruct-') as td:
    root=Path(td)
    srcgz=join_decode(M['source_bundle_parts'])
    assert hashlib.sha256(srcgz).hexdigest()==M['source_bundle_gzip_sha256']
    with tarfile.open(fileobj=io.BytesIO(srcgz),mode='r:gz') as tf: tf.extractall(root)
    bgz=join_decode(M['formal_batches_parts'])
    assert hashlib.sha256(bgz).hexdigest()==M['formal_batches_gzip_sha256']
    bdir=root/'batches'; bdir.mkdir()
    with tarfile.open(fileobj=io.BytesIO(bgz),mode='r:gz') as tf: tf.extractall(bdir)
    subprocess.run([sys.executable,str(root/'aggregate.py'),str(bdir),str(root/'FORMAL_AGGREGATE.json')],cwd=root,check=True)
    raw=(root/'FORMAL_AGGREGATE.json').read_bytes()
    got=hashlib.sha256(raw).hexdigest()
    assert got==M['formal_aggregate_raw_sha256'],(got,M['formal_aggregate_raw_sha256'])
    subprocess.run([sys.executable,str(root/'audit_a2.py'),str(root/'FORMAL_AGGREGATE.json'),str(bdir),'--out',str(root/'AUDIT.json')],cwd=root,check=True)
    print(json.dumps({'aggregate_sha256':got,'audit':json.loads((root/'AUDIT.json').read_text())},sort_keys=True))
