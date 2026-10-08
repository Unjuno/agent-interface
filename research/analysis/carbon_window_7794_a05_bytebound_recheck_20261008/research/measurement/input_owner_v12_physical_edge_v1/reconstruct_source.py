from pathlib import Path
import base64,hashlib,tarfile,io,json
root=Path(__file__).parent
manifest=json.loads((root/'SOURCE_MANIFEST.json').read_text())
b64=b''.join(p.read_bytes() for p in sorted(root.glob('source.part*.b64')))
if hashlib.sha256(b64).hexdigest()!=manifest['base64_sha256']: raise SystemExit('base64 hash mismatch')
raw=base64.b64decode(b64)
if hashlib.sha256(raw).hexdigest()!=manifest['tar_gz_sha256']: raise SystemExit('tar hash mismatch')
out=root/'reconstructed_source'; out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tf: tf.extractall(out)
for name,sha in manifest['files'].items():
    p=out/name
    if hashlib.sha256(p.read_bytes()).hexdigest()!=sha: raise SystemExit('file hash mismatch: '+name)
print('PASS',len(manifest['files']))
