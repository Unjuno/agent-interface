#!/usr/bin/env python3
from pathlib import Path
import base64, hashlib
HERE=Path(__file__).resolve().parent
raw=base64.b64decode(''.join((HERE/'evidence.tar.xz.b64').read_text().split()))
expected='e9b25c9527be2101ba8fe780847e06690ad24264dfd650473864453d188a3353'
actual=hashlib.sha256(raw).hexdigest()
if actual != expected: raise SystemExit(f'archive sha mismatch: {actual}')
out=HERE/'read_receipt_bypass_v1_evidence.tar.xz'; out.write_bytes(raw)
print(out, len(raw), actual)
