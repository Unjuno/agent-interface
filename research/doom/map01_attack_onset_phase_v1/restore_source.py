from pathlib import Path
import base64,hashlib,lzma,tarfile,io,json
root=Path(__file__).parent
freeze=json.loads((root/'FREEZE.json').read_text())
raw=base64.b64decode((root/'SOURCE.tar.xz.b64').read_text())
if hashlib.sha256(raw).hexdigest()!=freeze['source_capsule_sha256']:raise SystemExit('source capsule hash mismatch')
out=root/'restored_source';out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(lzma.decompress(raw)),mode='r:') as tf:tf.extractall(out)
print('PASS',hashlib.sha256(raw).hexdigest())
