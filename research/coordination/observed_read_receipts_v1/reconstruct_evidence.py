#!/usr/bin/env python3
from pathlib import Path
import base64, hashlib
HERE=Path(__file__).resolve().parent
raw=base64.b64decode(''.join((HERE/'evidence.tar.xz.b64').read_text().split()))
expected='26115b11e1c025ff25f74fff7bcd2613fc4eeb720bbbb53cbe904dcef6eccd5d'
actual=hashlib.sha256(raw).hexdigest()
if actual != expected: raise SystemExit(f'archive sha mismatch: {actual}')
out=HERE/'observed_read_receipts_v1_evidence.tar.xz'; out.write_bytes(raw)
print(out, len(raw), actual)
