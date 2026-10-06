from __future__ import annotations
import base64, hashlib, io, json, lzma, tarfile
from pathlib import Path
root=Path(__file__).resolve().parent
meta=json.loads((root/'CAPSULE.json').read_text())
blob=base64.b64decode((root/'EVIDENCE.b64').read_text())
if hashlib.sha256(blob).hexdigest()!=meta['decoded_sha256']: raise SystemExit('CAPSULE_SHA256_MISMATCH')
raw=lzma.decompress(blob)
if hashlib.sha256(raw).hexdigest()!=meta['uncompressed_tar_sha256']: raise SystemExit('TAR_SHA256_MISMATCH')
out=root/'restored'; out.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tf:
    for m in tf.getmembers():
        p=(out/m.name).resolve()
        if not str(p).startswith(str(out.resolve())+'/'): raise SystemExit('UNSAFE_PATH')
    tf.extractall(out)
print(json.dumps({'status':'restored','members':meta['members'],'decoded_sha256':meta['decoded_sha256']},sort_keys=True))
