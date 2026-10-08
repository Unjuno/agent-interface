# Audit reconstruction only; not a new scientific allocation.
from pathlib import Path
import base64, hashlib, json, subprocess, sys, tarfile, tempfile
HERE=Path(__file__).resolve().parent
M=json.loads((HERE/'RETENTION_MANIFEST.json').read_text())
raw=base64.b64decode((HERE/'SOURCE_BUNDLE.tar.gz.b64').read_text(encoding='ascii'))
assert hashlib.sha256(raw).hexdigest()==M['source_bundle_gzip_sha256']
with tempfile.TemporaryDirectory(prefix='ai24-status-reconstruct-') as td:
    root=Path(td); bundle=root/'source.tar.gz'; bundle.write_bytes(raw)
    with tarfile.open(bundle,'r:gz') as tf: tf.extractall(root/'src')
    src=root/'src'
    subprocess.run([sys.executable,str(src/'audit.py'),str(HERE/'FORMAL_RESULT.json'),'--out',str(root/'AUDIT.json')],cwd=src,check=True)
    got=json.loads((root/'AUDIT.json').read_text()); retained=json.loads((HERE/'AUDIT.json').read_text())
    assert got==retained
    print(json.dumps({'audit':got,'source_bundle_sha256':hashlib.sha256(raw).hexdigest()},sort_keys=True))
