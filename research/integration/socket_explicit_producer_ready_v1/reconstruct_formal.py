#!/usr/bin/env python3
import base64,hashlib,tarfile
from pathlib import Path
src=Path('FORMAL_EVIDENCE.tar.xz.b64'); raw=base64.b64decode(src.read_text())
expected=Path('EVIDENCE_SHA256.txt').read_text().split()[0]
actual=hashlib.sha256(raw).hexdigest()
if actual!=expected:raise SystemExit(f'archive hash mismatch: {actual}')
out=Path('formal_evidence.tar.xz');out.write_bytes(raw)
with tarfile.open(out,'r:xz') as tf:tf.extractall(Path('formal_evidence'),filter='data')
print(actual,len(raw))
