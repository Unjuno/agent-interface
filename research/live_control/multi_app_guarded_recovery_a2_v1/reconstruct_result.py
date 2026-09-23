#!/usr/bin/env python3
import base64,gzip,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
raw=gzip.decompress(base64.b64decode((HERE/'RESULT.json.gz.b64').read_text().strip()))
expected='9fbc5ab7aa2efcc885b92a17f0702fa71aec3bd2478ca6d956c2b7c4577fda17'
got=hashlib.sha256(raw).hexdigest()
if got!=expected: raise SystemExit(f'hash mismatch: {got}')
(HERE/'RESULT.reconstructed.json').write_bytes(raw)
print(got)
