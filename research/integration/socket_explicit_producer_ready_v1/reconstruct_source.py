#!/usr/bin/env python3
import base64,hashlib,tarfile
from pathlib import Path
src=Path('SOURCE_FREEZE.tar.xz.b64'); raw=base64.b64decode(src.read_text())
expected='2c4c5b3828db3f0becc0f1578f04bbda1c5d91e8db567930742e0d098e391fdc'
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:raise SystemExit(f'archive hash mismatch: {actual}')
out=Path('source_freeze.tar.xz');out.write_bytes(raw)
with tarfile.open(out,'r:xz') as tf:tf.extractall(Path('source_freeze'),filter='data')
print(actual,len(raw))
